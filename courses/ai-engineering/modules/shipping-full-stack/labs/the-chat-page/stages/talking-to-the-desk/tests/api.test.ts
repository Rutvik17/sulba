import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ApiError, Desk } from '#api.ts';

/** A fetch that answers each request with the next answer, and keeps the requests it was sent. */
function answering(...answers: Response[]) {
  const sent: Request[] = [];
  const fetcher = async (input: RequestInfo | URL, init?: RequestInit) => {
    sent.push(new Request(new URL(String(input), 'https://desk.test'), init));
    const answer = answers.shift();
    if (answer === undefined) throw new Error('No answer left.');
    return answer;
  };
  return { desk: new Desk(fetcher), sent };
}

function json(body: unknown, status = 200, type = 'application/json') {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': type } });
}

const conversation = { id: 'c1', page: 'dmv', messages: [] };

test('tst_vg2fwg A new conversation is posted as JSON, with its help pages', async () => {
  const { desk, sent } = answering(json(conversation, 201));
  assert.deepEqual(await desk.start('dmv'), conversation);
  const [request] = sent;
  assert.equal(request?.method, 'POST');
  assert.equal(request?.url, 'https://desk.test/conversations');
  assert.equal(request?.headers.get('Content-Type'), 'application/json');
  assert.equal(request?.headers.get('Accept'), 'application/json');
  assert.deepEqual(await request?.json(), { page: 'dmv' });
});

test('tst_lg2qtd A conversation and the list of them are asked for by GET, with no body', async () => {
  const summaries = [{ id: 'c1', page: null, started_at: '2026-10-22T09:00:00Z' }];
  const { desk, sent } = answering(json(conversation), json(summaries));
  assert.deepEqual(await desk.conversation('c1'), conversation);
  assert.deepEqual(await desk.conversations(), summaries);
  assert.deepEqual(
    sent.map((request) => [request.method, request.url, request.body]),
    [
      ['GET', 'https://desk.test/conversations/c1', null],
      ['GET', 'https://desk.test/conversations', null],
    ],
  );
});

test("tst_7uz0jj A conversation's id goes into the address encoded", async () => {
  const { desk, sent } = answering(json(conversation));
  await desk.conversation('a/b?c');
  assert.equal(sent[0]?.url, 'https://desk.test/conversations/a%2Fb%3Fc');
});

test('tst_tburyh An answer that is not a success throws its problem details', async () => {
  const problem = {
    type: 'about:blank',
    title: 'Unprocessable Content',
    status: 422,
    detail: 'The request has 1 problem.',
    errors: [{ detail: 'Input should be a valid string', pointer: '#/page' }],
  };
  const { desk } = answering(json(problem, 422, 'application/problem+json'));
  const error = await desk.start().then(
    () => assert.fail('The start should have failed.'),
    (thrown: unknown) => thrown,
  );
  assert.ok(error instanceof ApiError);
  assert.equal(error.status, 422);
  assert.equal(error.title, 'Unprocessable Content');
  assert.equal(error.detail, 'The request has 1 problem.');
  assert.deepEqual(error.errors, problem.errors);
});

test('tst_jt735a An error without problem details takes its status text', async () => {
  const { desk } = answering(
    new Response('<h1>Bad Gateway</h1>', { status: 502, statusText: 'Bad Gateway' }),
  );
  await assert.rejects(desk.me(), (error: unknown) => {
    assert.ok(error instanceof ApiError);
    assert.deepEqual([error.status, error.title, error.detail], [502, 'Bad Gateway', null]);
    return true;
  });
});

test('tst_2md61j The usage covers from 1 to 90 days, and asks for that many', async () => {
  const { desk, sent } = answering(json([]));
  assert.deepEqual(await desk.usage(30), []);
  assert.equal(sent[0]?.url, 'https://desk.test/usage?days=30');
  for (const days of [0, 91, 2.5]) await assert.rejects(desk.usage(days), RangeError);
  assert.equal(sent.length, 1);
});

test("tst_cvm5mc A message is posted for the reply's event stream, with the caller's signal", async () => {
  const stream = new Response('event: done\ndata: {}\n\n', {
    headers: { 'Content-Type': 'text/event-stream' },
  });
  const { desk, sent } = answering(stream);
  const leaving = new AbortController();
  assert.equal(await desk.say('c1', 'When do you open?', leaving.signal), stream);
  const [request] = sent;
  assert.equal(request?.url, 'https://desk.test/conversations/c1/messages');
  assert.equal(request?.headers.get('Accept'), 'text/event-stream');
  assert.deepEqual(await request?.json(), { content: 'When do you open?' });
  leaving.abort();
  assert.equal(request?.signal.aborted, true);
});

test('tst_uvvdd9 A message the desk refuses throws, as a JSON request does', async () => {
  const busy = { type: 'about:blank', title: 'Service Unavailable', status: 503 };
  const { desk } = answering(json(busy, 503, 'application/problem+json'));
  await assert.rejects(desk.say('c1', 'Hello'), (error: unknown) => {
    assert.ok(error instanceof ApiError);
    assert.deepEqual([error.status, error.title], [503, 'Service Unavailable']);
    return true;
  });
});

test("tst_pgwcvd The browser's fetch is called on its own, not as a method of the desk", async () => {
  let receiver: unknown = 'not called';
  function fetcher(this: unknown) {
    receiver = this;
    return Promise.resolve(json(conversation));
  }
  await new Desk(fetcher as typeof fetch).conversation('c1');
  assert.equal(receiver, undefined);
});
