import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { Window } from 'happy-dom';
import { type Conversation, Desk } from '#api.ts';
import { Chat, type ChatElements } from '#chat.ts';

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

/** Each message on the page, as who said it and what they said. */
function shown(elements: ChatElements): { role?: string; who?: string; text?: string }[] {
  return [...elements.log.children].map((message) => {
    const element = message as HTMLElement;
    const who = element.querySelector('.who')?.textContent;
    const text = element.querySelector('.text')?.textContent;
    return {
      ...(element.dataset.role === undefined ? {} : { role: element.dataset.role }),
      ...(who === undefined || who === null ? {} : { who }),
      ...(text === undefined || text === null ? {} : { text }),
    };
  });
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
  const sent: { url: string; content: unknown; signal: AbortSignal | null }[] = [];
  const fetcher: typeof fetch = async (input, init) => {
    const signal = init?.signal ?? null;
    sent.push({ url: String(input), content: JSON.parse(String(init?.body)), signal });
    return new Response(body, { headers: { 'Content-Type': 'text/event-stream' } });
  };
  return { desk: new Desk(fetcher), sent };
}

/** Lets what the page does with the events sent so far happen. */
const settle = () => new Promise((resolve) => setTimeout(resolve, 10));

test('tst_urabb2 Each message of the conversation is on the page, with who said it', () => {
  const elements = page();
  new Chat(desk(line().body).desk, conversation, elements);
  assert.deepEqual(shown(elements), [
    { role: 'caller', who: 'You', text: 'How do I replace a lost card?' },
    { role: 'desk', who: 'The desk', text: 'You can ask for a new card online.' },
  ]);
});

test('tst_97yh1a A message is put on the page as text, never as markup', () => {
  const elements = page();
  const content = '<img src="x" onerror="alert(1)"> & <b>now</b>';
  const odd: Conversation = { id: 'c1', page: null, messages: [{ role: 'desk', content }] };
  new Chat(desk(line().body).desk, odd, elements);
  assert.equal(elements.log.querySelectorAll('img, b').length, 0);
  assert.deepEqual(shown(elements), [{ role: 'desk', who: 'The desk', text: content }]);
});

test("tst_zbneoq The caller's message shows at once, and the reply grows as its text comes", async () => {
  const elements = page();
  const reply = line();
  const chat = new Chat(desk(reply.body).desk, conversation, elements);
  elements.input.value = '  When does it come?  ';
  const sending = chat.send(elements.input.value);
  await settle();
  assert.equal(elements.input.value, '');
  assert.deepEqual(shown(elements).slice(2), [
    { role: 'caller', who: 'You', text: 'When does it come?' },
    { role: 'desk', who: 'The desk', text: '' },
  ]);
  reply.event('text', { delta: 'In about ' });
  await settle();
  assert.equal(shown(elements)[3]?.text, 'In about ');
  reply.event('tool', { name: 'search' });
  reply.event('text', { delta: '14 days' });
  await settle();
  assert.equal(shown(elements)[3]?.text, 'In about 14 days');
  reply.event('done', { content: 'In about 14 days.' });
  await sending;
  assert.equal(shown(elements)[3]?.text, 'In about 14 days.');
  assert.equal(elements.log.children.length, 4);
});

test('tst_8olh55 While the reply comes, the log is busy and Send is off, and after, both are back', async () => {
  const elements = page();
  const reply = line();
  const chat = new Chat(desk(reply.body).desk, conversation, elements);
  const sending = chat.send('When does it come?');
  await settle();
  assert.equal(elements.log.getAttribute('aria-busy'), 'true');
  assert.equal(elements.send.disabled, true);
  reply.event('done', { content: 'In about 14 days.' });
  await sending;
  assert.equal(elements.log.getAttribute('aria-busy'), 'false');
  assert.equal(elements.send.disabled, false);
});

test("tst_dzak6f Sending the form sends what's in the box, and the page stays where it is", async () => {
  const elements = page();
  const reply = line();
  const { desk: theDesk, sent } = desk(reply.body);
  new Chat(theDesk, conversation, elements);
  let stayed = false;
  elements.form.addEventListener('submit', (event) => {
    stayed = event.defaultPrevented;
  });
  elements.input.value = 'When does it come?';
  elements.form.requestSubmit();
  assert.equal(stayed, true, 'The browser would send the form and leave the page.');
  await settle();
  assert.deepEqual(
    sent.map(({ url, content }) => ({ url, content })),
    [{ url: '/conversations/c1/messages', content: { content: 'When does it come?' } }],
  );
  reply.event('done', { content: 'In about 14 days.' });
});

test("tst_kz2rx2 A blank message, or one sent while a reply comes, isn't sent", async () => {
  const elements = page();
  const reply = line();
  const { desk: theDesk, sent } = desk(reply.body);
  const chat = new Chat(theDesk, conversation, elements);
  await chat.send(' \n ');
  assert.equal(sent.length, 0);
  const sending = chat.send('When does it come?');
  await settle();
  await chat.send('Hello?');
  assert.equal(sent.length, 1);
  reply.event('done', { content: 'In about 14 days.' });
  await sending;
  assert.equal(elements.log.children.length, 4);
});

test('tst_kbewbm A reply that fails takes its turn off the page and gives the message back', async () => {
  const elements = page();
  const reply = line();
  const chat = new Chat(desk(reply.body).desk, conversation, elements);
  const sending = chat.send('When does it come?');
  await settle();
  reply.event('text', { delta: 'In about' });
  reply.event('error', { title: 'The reply took too long.' });
  await sending;
  assert.equal(elements.log.children.length, 2);
  assert.equal(elements.input.value, 'When does it come?');
  assert.equal(elements.status.textContent, 'The reply took too long.');
  assert.equal(elements.log.getAttribute('aria-busy'), 'false');
  assert.equal(elements.send.disabled, false);
});

test("tst_doqkl5 An answer that isn't a success shows its problem, until a message gets a reply", async () => {
  const elements = page();
  const reply = line();
  let calls = 0;
  const fetcher: typeof fetch = async () => {
    calls += 1;
    if (calls === 1) {
      const problem = {
        type: 'about:blank',
        title: 'Service Unavailable',
        status: 503,
        detail: 'The desk is answering as many callers as it can.',
      };
      return new Response(JSON.stringify(problem), {
        status: 503,
        headers: { 'Content-Type': 'application/problem+json', 'Retry-After': '30' },
      });
    }
    return new Response(reply.body, { headers: { 'Content-Type': 'text/event-stream' } });
  };
  const chat = new Chat(new Desk(fetcher), conversation, elements);
  await chat.send('When does it come?');
  assert.equal(elements.status.textContent, 'The desk is answering as many callers as it can.');
  assert.equal(elements.input.value, 'When does it come?');
  assert.equal(elements.log.children.length, 2);
  const sending = chat.send(elements.input.value);
  await settle();
  assert.equal(elements.status.textContent, '');
  reply.event('done', { content: 'In about 14 days.' });
  await sending;
  assert.equal(elements.log.children.length, 4);
});

test("tst_sfq4yx A desk that can't be reached shows that the message wasn't sent", async () => {
  const elements = page();
  const fetcher: typeof fetch = async () => {
    throw new TypeError('Failed to fetch');
  };
  const chat = new Chat(new Desk(fetcher), conversation, elements);
  await chat.send('When does it come?');
  assert.equal(elements.status.textContent, "The message couldn't be sent.");
  assert.equal(elements.input.value, 'When does it come?');
  assert.equal(elements.log.children.length, 2);
  assert.equal(elements.send.disabled, false);
});

test('tst_fhwntz Closing the chat stops the reply that is coming, and takes no more messages', async () => {
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
  reply.event('text', { delta: 'In about' });
  await settle();
  chat.close();
  assert.equal(signal.aborted, true);
  const stopped = await Promise.race([sending.then(() => true), settle().then(() => false)]);
  assert.equal(stopped, true, 'The reply is still coming.');
  assert.equal(elements.status.textContent, '');
  assert.equal(elements.log.children.length, 2);
  elements.input.value = 'Hello?';
  elements.form.requestSubmit();
  await settle();
  assert.equal(sent.length, 1, 'A closed chat sent a message.');
});
