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

test("tst_8ga814 Shows the conversation's messages", () => {
  const elements = page();
  new Chat(desk(line().body).desk, conversation, elements);
  assert.deepEqual(said(elements), [
    'How do I replace a lost card?',
    'You can ask for a new card online.',
  ]);
});

test('tst_s10m2h Shows the reply as it comes, then the whole of it', async () => {
  const elements = page();
  const reply = line();
  const chat = new Chat(desk(reply.body).desk, conversation, elements);
  const sending = chat.send('When does it come?');
  reply.event('text', { delta: 'In about ' });
  reply.event('text', { delta: '14 days' });
  await settle();
  assert.deepEqual(said(elements).slice(2), ['When does it come?', 'In about 14 days']);
  reply.event('done', { content: 'In about 14 days.' });
  await sending;
  assert.deepEqual(said(elements).slice(2), ['When does it come?', 'In about 14 days.']);
});

test('tst_30gmpg Turns Send off while the reply comes, and on again after it', async () => {
  const elements = page();
  const reply = line();
  const chat = new Chat(desk(reply.body).desk, conversation, elements);
  const sending = chat.send('When does it come?');
  await settle();
  assert.equal(elements.send.disabled, true);
  reply.event('done', { content: 'In about 14 days.' });
  await sending;
  assert.equal(elements.send.disabled, false);
});

test("tst_tvfhh1 Shows a failed reply's problem, and gives the message back", async () => {
  const elements = page();
  const reply = line();
  const chat = new Chat(desk(reply.body).desk, conversation, elements);
  const sending = chat.send('When does it come?');
  reply.event('error', { title: 'The reply took too long.' });
  await sending;
  assert.equal(elements.status.textContent, 'The reply took too long.');
  assert.equal(elements.input.value, 'When does it come?');
  assert.equal(elements.log.children.length, 2);
});

test("tst_asfbdp Doesn't send a blank message", async () => {
  const elements = page();
  const { desk: theDesk, sent } = desk(line().body);
  const chat = new Chat(theDesk, conversation, elements);
  await chat.send('  ');
  assert.equal(sent.length, 0);
});
