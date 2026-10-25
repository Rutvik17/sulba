import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { Window } from 'happy-dom';
import { type Conversation, Desk } from '#api.ts';
import type { ChatElements } from '#chat.ts';
import { Chat } from '#desk_chat.ts';

const windows: Window[] = [];
after(async () => {
  for (const window of windows) await window.happyDOM.close();
});

/** The chat's part of the page, as the desk's page has it. */
function page(): ChatElements {
  const window = new Window({ url: 'https://desk.test/' });
  windows.push(window);
  const document = window.document as unknown as Document;
  document.body.innerHTML = `
    <div id="log" role="log" aria-live="polite" aria-label="Conversation"></div>
    <form>
      <label for="content">Message</label>
      <textarea id="content" name="content" maxlength="2000"></textarea>
      <button type="submit">Send</button>
    </form>
    <p id="status" role="status" aria-live="polite"></p>`;
  const found = <T extends Element>(selector: string): T => {
    const element = document.querySelector<T>(selector);
    assert.ok(element, `The page has no ${selector}.`);
    return element;
  };
  return {
    log: found('#log'),
    form: found('form'),
    input: found('textarea'),
    send: found('button'),
    status: found('#status'),
  };
}

const conversation: Conversation = {
  id: 'c1',
  page: 'ssa',
  messages: [
    { role: 'caller', content: 'How do I replace a lost card?' },
    { role: 'desk', content: 'You can ask for a new card online.' },
  ],
};

/** What each message on the page says. */
function said(elements: ChatElements): (string | null | undefined)[] {
  return [...elements.log.children].map((message) => message.querySelector('.text')?.textContent);
}

/** A reply's event stream that the test sends events on, one at a time. */
function line() {
  const encoder = new TextEncoder();
  let controller!: ReadableStreamDefaultController<Uint8Array>;
  const body = new ReadableStream<Uint8Array>({
    start(given) {
      controller = given;
    },
  });
  return {
    body,
    event(type: string, data: object) {
      controller.enqueue(encoder.encode(`event: ${type}\ndata: ${JSON.stringify(data)}\n\n`));
    },
    fail(reason: unknown) {
      controller.error(reason);
    },
  };
}

/** A desk whose replies come from the stream, with each request it was sent. */
function desk(body: ReadableStream<Uint8Array>) {
  const sent: { content: unknown; signal: AbortSignal | null }[] = [];
  const fetcher: typeof fetch = async (_input, init) => {
    sent.push({ content: JSON.parse(String(init?.body)), signal: init?.signal ?? null });
    return new Response(body, { headers: { 'Content-Type': 'text/event-stream' } });
  };
  return { desk: new Desk(fetcher), sent };
}

/** Lets what the page does with the events sent so far happen. */
const settle = () => new Promise((resolve) => setTimeout(resolve, 10));

test('tst_2yik02 A reply with markup in it is shown as text', async () => {
  const elements = page();
  const reply = line();
  const chat = new Chat(desk(reply.body).desk, conversation, elements);
  const sending = chat.send('Where do I apply?');
  // A model can be led to write markup, by a help page's text or by the caller.
  const content = 'At <a href="https://www.ssa.gov">SSA</a>.<img src="x" onerror="alert(1)">';
  reply.event('done', { content });
  await sending;
  assert.equal(elements.log.querySelectorAll('a, img').length, 0);
  assert.equal(said(elements)[3], content);
});

test('tst_q5gt3f The status stays quiet while the reply comes', async () => {
  const elements = page();
  const reply = line();
  const chat = new Chat(desk(reply.body).desk, conversation, elements);
  const sending = chat.send('When does it come?');
  for (const delta of ['In', ' about', ' 14', ' days']) {
    reply.event('text', { delta });
    await settle();
    assert.equal(elements.status.textContent, '', 'A screen reader reads out every piece.');
  }
  reply.event('done', { content: 'In about 14 days.' });
  await sending;
});

test('tst_9azm5o After a reply fails, Send is on again', async () => {
  const elements = page();
  const reply = line();
  const chat = new Chat(desk(reply.body).desk, conversation, elements);
  const sending = chat.send('When does it come?');
  reply.event('text', { delta: 'In about' });
  reply.event('error', { title: 'The reply took too long.' });
  await sending;
  assert.equal(elements.send.disabled, false);
});

test('tst_g1i94n Opening another conversation stops the reply at once', async () => {
  const elements = page();
  const reply = line();
  const { desk: theDesk, sent } = desk(reply.body);
  const chat = new Chat(theDesk, conversation, elements);
  const sending = chat.send('When does it come?');
  await settle();
  const signal = sent[0]?.signal;
  assert.ok(signal, 'The request has no signal to stop it with.');
  // As the browser's fetch does, the body fails once its request is stopped.
  signal.addEventListener('abort', () => reply.fail(signal.reason));
  // The desk is searching its help pages, and sends nothing for now.
  chat.close();
  assert.equal(signal.aborted, true, 'The request goes on, and keeps its place at the desk.');
  const stopped = await Promise.race([sending.then(() => true), settle().then(() => false)]);
  assert.equal(stopped, true, 'The reply is still coming.');
});
