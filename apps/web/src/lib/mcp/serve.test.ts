import { createLocalJWKSet, exportJWK, generateKeyPair, type JWTPayload, SignJWT } from 'jose';
import { beforeAll, expect, test } from 'vitest';
import { metadataOf, metadataPath, type Settings, serveMcp } from './serve';
import { proofText } from './tools';

// A key that stands in for the Supabase project's, and the Data API's answers for one workspace.
const pair = await generateKeyPair('ES256');
const supabaseUrl = 'https://project.supabase.co';
const origin = 'https://sulba.dev';
const person = 'a0000000-0000-4000-8000-000000000001';
let keys: Settings['keys'];
beforeAll(async () => {
  keys = createLocalJWKSet({
    keys: [{ ...(await exportJWK(pair.publicKey)), kid: 'project', alg: 'ES256' }],
  });
});

const agentClaims = {
  sub: person,
  role: 'authenticated',
  client_id: 'e0000000-0000-4000-8000-000000000005',
};

function token(
  payload: JWTPayload = agentClaims,
  { from = `${supabaseUrl}/auth/v1`, expires = '1h' } = {},
) {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: 'ES256', kid: 'project' })
    .setIssuer(from)
    .setAudience('authenticated')
    .setIssuedAt()
    .setExpirationTime(expires)
    .sign(pair.privateKey);
}

const workspace = { id: 'w1', name: 'Acme', slug: 'acme' };
const spec = {
  id: 's1',
  number: 3,
  title: 'Retry failed payments',
  status: 'approved',
  body: 'Payments fail for many reasons.',
  owner_id: person,
  created_at: '2026-10-28T00:00:00Z',
  updated_at: '2026-10-28T00:00:00Z',
  criteria: [
    { id: 'c1', number: 1, text: 'Retries once after 30 seconds' },
    { id: 'c2', number: 2, text: 'Keeps the idempotency key' },
  ],
};
const bookingApp = {
  id: 'r1',
  number: 2,
  title: 'A booking app',
  status: 'open',
  body: 'Members book classes from their phones.',
  created_by: person,
  created_at: '2026-10-30T00:00:00Z',
  updated_at: '2026-10-30T00:00:00Z',
  questions: [
    {
      id: 'q1',
      text: 'Do members pay when they book?',
      answer: 'Yes, by card.',
      asked_by: person,
      asked_by_agent: 'Claude Code',
      answered_by: person,
      asked_at: '2026-10-30T00:00:00Z',
      answered_at: '2026-10-30T01:00:00Z',
    },
    {
      id: 'q2',
      text: 'Can a member cancel?',
      answer: null,
      asked_by: person,
      asked_by_agent: 'Claude Code',
      answered_by: null,
      asked_at: '2026-10-30T02:00:00Z',
      answered_at: null,
    },
  ],
  specs: [{ number: 3, title: 'Retry failed payments', status: 'approved' }],
};
const bookingTask = {
  id: 't1',
  number: 7,
  title: 'Build the retry job',
  role: 'build',
  status: 'blocked',
  body: 'Add the job to the payments worker.',
  note: 'Which queue should it use?',
  taken_by: person,
  taken_by_agent: 'Claude Code',
  taken_at: '2026-10-30T03:00:00Z',
  pull_request: null,
  created_by: person,
  created_by_agent: 'Claude Code',
  created_at: '2026-10-30T02:00:00Z',
  updated_at: '2026-10-30T03:00:00Z',
  specs: { id: 's1', number: 3, title: 'Retry failed payments', status: 'approved' },
  task_criteria: [
    { criteria: { number: 2, text: 'Keeps the idempotency key' } },
    { criteria: { number: 1, text: 'Retries once after 30 seconds' } },
  ],
};
const proof = (n: number, state: string, counts: { passed: number; failed: number }) => ({
  criterion_id: `c${n}`,
  workspace_id: 'w1',
  spec_id: 's1',
  spec_number: 3,
  spec_title: spec.title,
  spec_status: 'approved',
  criterion_number: n,
  text: spec.criteria[n - 1]?.text,
  suspect_since: null,
  tests: counts.passed + counts.failed,
  ...counts,
  skipped: 0,
  state,
  checked_at: '2026-10-28T00:00:00Z',
});

/**
 * Supabase as the server asks it: the Auth server about the agent's session, and the Data API
 * as PostgREST answers these reads, keeping the requests it was sent.
 */
function standIn({
  refuse,
  disconnected = false,
  releases = [],
}: {
  refuse?: { code: string; message: string };
  disconnected?: boolean;
  releases?: object[];
} = {}) {
  const sent: Request[] = [];
  const fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = new Request(input, init);
    sent.push(request);
    const path = new URL(request.url).pathname;
    const one = request.headers.get('Accept')?.includes('vnd.pgrst.object') ?? false;
    const json = (body: unknown, status = 200) => Response.json(body, { status });
    if (path === '/auth/v1/user') {
      return disconnected
        ? json({ code: 403, error_code: 'session_not_found', msg: 'Session not found' }, 403)
        : json({ id: person, aud: 'authenticated' });
    }
    if (refuse && request.method !== 'GET')
      return json({ ...refuse, details: null, hint: null }, 403);
    if (path.endsWith('/members')) {
      if (new URL(request.url).searchParams.get('select')?.includes('people')) {
        return json([
          {
            person_id: person,
            role: 'owner',
            joined_at: '2026-10-28T00:00:00Z',
            people: { name: 'Ada Lovelace', email: 'ada@example.com' },
          },
        ]);
      }
      const row = { role: 'member', workspaces: workspace };
      return json(one ? row : [row]);
    }
    if (path.endsWith('/specs')) return json(one ? spec : [spec]);
    if (path.endsWith('/requests')) {
      // The list counts each request's specs; reading one lists them.
      const counted = new URL(request.url).searchParams.get('select')?.includes('specs(count)');
      return json([counted ? { ...bookingApp, specs: [{ count: 1 }] } : bookingApp]);
    }
    if (path.endsWith('/rpc/ask_question')) return json('q3');
    if (path.endsWith('/releases')) return json(releases);
    if (path.endsWith('/tasks')) return json(one ? bookingTask : [bookingTask]);
    if (path.endsWith('/rpc/create_task')) return json(8);
    if (path.endsWith('/rpc/update_task')) return new Response(null, { status: 204 });
    if (path.endsWith('/rpc/create_spec')) return json(4);
    if (path.endsWith('/spec_reviews')) {
      return json([
        { verdict: 'approved', note: null, people: { name: 'Ben Ortiz', email: null } },
        {
          verdict: 'changes_requested',
          note: 'Say how long it waits',
          people: { name: '', email: 'cy@example.com' },
        },
      ]);
    }
    if (path.endsWith('/criterion_proofs')) {
      return json([
        proof(1, 'proven', { passed: 2, failed: 0 }),
        proof(2, 'failing', { passed: 0, failed: 1 }),
      ]);
    }
    if (path.endsWith('/latest_claims')) {
      return json([
        {
          id: 1,
          spec_number: 3,
          criterion_number: 2,
          name: 'test_SPEC_3_AC_2_keeps_the_key',
          classname: 'tests.test_pay',
          file: null,
          outcome: 'failed',
          message: "assert 'k2' == 'k1'",
          repository: 'acme-co/payments',
          suite: 'unit',
          sha: 'a1b2c3d4e5f60718293a4b5c6d7e8f9012345678',
          run_id: 1000,
          workflow: 'CI',
          received_at: '2026-10-28T00:00:00Z',
        },
      ]);
    }
    return json({ code: 'PGRST', message: 'not found' }, 404);
  };
  return { fetch, sent };
}

let calls = 0;
async function mcp(
  body: object,
  {
    bearer,
    headers = {},
    fetch = standIn().fetch,
  }: { bearer?: string; headers?: Record<string, string>; fetch?: typeof globalThis.fetch } = {},
) {
  const response = await serveMcp(
    new Request(`${origin}/mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json, text/event-stream',
        'MCP-Protocol-Version': '2025-11-25',
        ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
        ...headers,
      },
      body: JSON.stringify({ jsonrpc: '2.0', id: ++calls, ...body }),
    }),
    { supabaseUrl, publishableKey: 'sb_publishable_test', ...(keys ? { keys } : {}), fetch },
  );
  return response;
}

/** The JSON-RPC answer, sent as JSON or as one server-sent event. */
async function read<T>(response: Response): Promise<T> {
  const text = await response.text();
  const data = text.startsWith('{')
    ? text
    : text
        .split('\n')
        .find((line) => line.startsWith('data: '))
        ?.slice(6);
  return JSON.parse(data ?? '{}') as T;
}

const tool = async (name: string, args: object, fetch?: typeof globalThis.fetch) => {
  const response = await mcp(
    { method: 'tools/call', params: { name, arguments: args } },
    { bearer: await token(), ...(fetch ? { fetch } : {}) },
  );
  const { result } = await read<{ result: { content: { text: string }[]; isError?: boolean } }>(
    response,
  );
  return { text: result.content[0]?.text ?? '', isError: result.isError ?? false };
};

test('the metadata names the server and where agents sign in', async () => {
  const body = await metadataOf(origin, { supabaseUrl, publishableKey: 'k' }).json();
  expect(body).toMatchObject({
    resource: 'https://sulba.dev/mcp',
    authorization_servers: ['https://project.supabase.co/auth/v1'],
  });
});

test('a request without a token is told where to sign in', async () => {
  const response = await mcp({ method: 'tools/list' });
  expect(response.status).toBe(401);
  expect(response.headers.get('WWW-Authenticate')).toContain(
    `resource_metadata="${origin}${metadataPath}"`,
  );
});

test('a browser session’s token, another issuer’s or an expired one is refused', async () => {
  const { client_id: _, ...session } = agentClaims;
  for (const bearer of [
    await token(session),
    await token(agentClaims, { from: 'https://other.supabase.co/auth/v1' }),
    await token(agentClaims, { expires: '-1m' }),
  ]) {
    expect((await mcp({ method: 'tools/list' }, { bearer })).status).toBe(401);
  }
});

test('a disconnected agent is told to sign in again, though its token hasn’t expired', async () => {
  const response = await mcp(
    { method: 'tools/list' },
    { bearer: await token(), fetch: standIn({ disconnected: true }).fetch },
  );
  expect(response.status).toBe(401);
  expect(response.headers.get('WWW-Authenticate')).toContain(
    'This agent was disconnected. Sign it in again from its MCP settings',
  );
});

test('a page on another site can’t call the server through a browser', async () => {
  const response = await mcp(
    { method: 'tools/list' },
    { bearer: await token(), headers: { Origin: 'https://evil.example' } },
  );
  expect(response.status).toBe(403);
});

test('an agent on the 2025 protocol starts a session and lists the tools, reads marked read-only', async () => {
  const bearer = await token();
  const init = await mcp(
    {
      method: 'initialize',
      params: {
        protocolVersion: '2025-11-25',
        capabilities: {},
        clientInfo: { name: 'test', version: '1' },
      },
    },
    { bearer },
  );
  const { result } = await read<{ result: { serverInfo: { name: string }; instructions: string } }>(
    init,
  );
  expect(result.serverInfo.name).toBe('sulba');
  expect(result.instructions).toContain('test_SPEC_12_AC_3');

  const list = await read<{
    result: { tools: { name: string; annotations: { readOnlyHint: boolean } }[] };
  }>(await mcp({ method: 'tools/list' }, { bearer }));
  expect(list.result.tools.map((each) => each.name)).toEqual([
    'list_workspaces',
    'list_specs',
    'get_spec',
    'create_spec',
    'update_spec',
    'add_criterion',
    'reword_criterion',
    'list_requests',
    'get_request',
    'ask_question',
    'get_release',
    'list_tasks',
    'get_task',
    'create_task',
    'take_task',
    'update_task',
    'get_evidence',
  ]);
  expect(
    list.result.tools.filter((each) => each.annotations.readOnlyHint).map((each) => each.name),
  ).toEqual([
    'list_workspaces',
    'list_specs',
    'get_spec',
    'list_requests',
    'get_request',
    'get_release',
    'list_tasks',
    'get_task',
    'get_evidence',
  ]);
});

test('an agent on the 2026-07-28 protocol calls a tool with no handshake, naming it in a header', async () => {
  const bearer = await token();
  const meta = {
    'io.modelcontextprotocol/protocolVersion': '2026-07-28',
    'io.modelcontextprotocol/clientCapabilities': {},
    'io.modelcontextprotocol/clientInfo': { name: 'test', version: '1' },
  };
  const modern = (method: string, params: object, name?: string) =>
    mcp(
      { method, params: { ...params, _meta: meta } },
      {
        bearer,
        headers: {
          'MCP-Protocol-Version': '2026-07-28',
          'Mcp-Method': method,
          ...(name ? { 'Mcp-Name': name } : {}),
        },
      },
    );

  const discovered = await read<{ result: { supportedVersions: string[] } }>(
    await modern('server/discover', {}),
  );
  expect(discovered.result.supportedVersions).toContain('2026-07-28');
  const called = await read<{ result: { content: { text: string }[] } }>(
    await modern('tools/call', { name: 'list_workspaces', arguments: {} }, 'list_workspaces'),
  );
  expect(called.result.content[0]?.text).toBe('- acme: Acme (member)');
  const unnamed = await modern('tools/call', { name: 'list_workspaces', arguments: {} });
  expect(unnamed.status).toBe(400);
});

test('get_spec gives the criteria with their proof, what a failing test said and the review, asking as the agent', async () => {
  const supabase = standIn();
  const { text } = await tool('get_spec', { workspace: 'acme', spec: 'spec-3' }, supabase.fetch);
  expect(text).toContain('# SPEC-3: Retry failed payments');
  expect(text).toContain('Status: Approved. https://sulba.dev/app/acme/SPEC-3');
  expect(text).toContain('- SPEC-3/AC-1: Retries once after 30 seconds (Proven by 2 tests)');
  expect(text).toContain('- SPEC-3/AC-2: Keeps the idempotency key (Failing: 1 of 1 test failed)');
  expect(text).toContain(
    "  - test_SPEC_3_AC_2_keeps_the_key failed in acme-co/payments at a1b2c3d: assert 'k2' == 'k1'",
  );
  expect(text).toContain(
    '## Review\n\n- Ben Ortiz: Approved\n- cy@example.com: Asked for changes: “Say how long it waits”',
  );
  const bearer = `Bearer ${await token()}`.slice(0, 20);
  expect(
    supabase.sent.every((request) => request.headers.get('Authorization')?.startsWith(bearer)),
  ).toBe(true);
});

test('get_request gives the writer’s words, each question with its answer, and the specs drafted', async () => {
  const { text } = await tool('get_request', { workspace: 'acme', request: 'req-2' });
  expect(text).toContain('# REQ-2: A booking app');
  expect(text).toContain('Status: Open. https://sulba.dev/app/acme/REQ-2');
  expect(text).toContain('Members book classes from their phones.');
  expect(text).toContain('- Do members pay when they book?\n  Answer: Yes, by card.');
  expect(text).toContain('- Can a member cancel?\n  Not answered yet.');
  expect(text).toContain('## Specs drafted from it\n\n- SPEC-3: Retry failed payments (Approved)');
});

test('list_requests counts each request’s unanswered questions and drafted specs', async () => {
  const { text } = await tool('list_requests', { workspace: 'acme' });
  expect(text).toBe(
    '- REQ-2: A booking app (Open; 1 question waits for an answer; 1 spec drafted)',
  );
});

test('an agent asks about a request, and drafts a spec that names it', async () => {
  const supabase = standIn();
  const asked = await tool(
    'ask_question',
    { workspace: 'acme', request: 'REQ-2', question: ' Can a member cancel? ' },
    supabase.fetch,
  );
  expect(asked.text).toBe(
    'Asked about REQ-2. Its writer answers in Sulba. https://sulba.dev/app/acme/REQ-2',
  );
  const drafted = await tool(
    'create_spec',
    {
      workspace: 'acme',
      title: 'Book a class',
      criteria: ['A member books a class from the timetable'],
      request: 'REQ-2',
    },
    supabase.fetch,
  );
  expect(drafted.text).toBe('Wrote SPEC-4 as a draft. https://sulba.dev/app/acme/SPEC-4');
  const bodies = await Promise.all(
    supabase.sent
      .filter((each) => new URL(each.url).pathname.includes('/rpc/'))
      .map(async (each) => [new URL(each.url).pathname.split('/').at(-1), await each.json()]),
  );
  expect(bodies).toEqual([
    ['ask_question', { request: 'r1', text: 'Can a member cancel?' }],
    [
      'create_spec',
      {
        workspace: 'w1',
        title: 'Book a class',
        criteria: ['A member books a class from the timetable'],
        request: 'r1',
      },
    ],
  ]);
});

test('get_release says what stands between a request and its release until one is approved', async () => {
  const { text } = await tool('get_release', { workspace: 'acme', request: 'REQ-2' });
  expect(text).toBe(
    [
      'REQ-2 has no release yet. A person approves one in Sulba.',
      '',
      'Before it can be approved:',
      '- SPEC-3 has 1 of 2 criteria not proven yet: AC-2.',
    ].join('\n'),
  );
});

test('get_release gives the latest release’s document, naming who approved it', async () => {
  const supabase = standIn({
    releases: [
      {
        id: 'rel2',
        number: 2,
        note: null,
        approved_by: person,
        approved_at: '2026-10-31T09:00:00Z',
        snapshot: [
          {
            number: 3,
            title: 'Retry failed payments',
            status: 'implemented',
            criteria: [{ number: 1, text: 'Retries once after 30 seconds', tests: 2 }],
            tasks: [],
          },
        ],
      },
    ],
  });
  const { text } = await tool(
    'get_release',
    { workspace: 'acme', request: 'REQ-2' },
    supabase.fetch,
  );
  expect(text.split('\n').slice(0, 3)).toEqual([
    '# REQ-2 A booking app: release 2',
    '',
    'Approved by Ada Lovelace on October 31, 2026 (UTC).',
  ]);
  expect(text).toContain('| AC-1 Retries once after 30 seconds | 2 tests |');
});

test('get_task gives the task’s spec, status, what blocks it, its instructions and its criteria in order', async () => {
  const { text } = await tool('get_task', { workspace: 'acme', task: 'task-7' });
  expect(text).toBe(
    [
      '# TASK-7: Build the retry job',
      '',
      'Build for SPEC-3, Retry failed payments. Status: Blocked. https://sulba.dev/app/acme/TASK-7',
      '',
      'Blocked: Which queue should it use?',
      '',
      'Add the job to the payments worker.',
      '',
      '## Criteria it covers',
      '',
      '- SPEC-3/AC-1: Retries once after 30 seconds',
      '- SPEC-3/AC-2: Keeps the idempotency key',
    ].join('\n'),
  );
});

test('an agent writes a task, takes one and hands it in with its pull request', async () => {
  const supabase = standIn();
  const wrote = await tool(
    'create_task',
    { workspace: 'acme', spec: 'SPEC-3', title: 'Test the retry job', role: 'test', criteria: [1] },
    supabase.fetch,
  );
  expect(wrote.text).toBe('Wrote TASK-8. https://sulba.dev/app/acme/TASK-8');
  const took = await tool('take_task', { workspace: 'acme', task: 'TASK-7' }, supabase.fetch);
  expect(took.text).toBe('Took TASK-7. https://sulba.dev/app/acme/TASK-7');
  const handed = await tool(
    'update_task',
    {
      workspace: 'acme',
      task: 'TASK-7',
      status: 'in_review',
      pull_request: 'https://github.com/acme-co/payments/pull/12',
    },
    supabase.fetch,
  );
  expect(handed.text).toBe('TASK-7 is in review. https://sulba.dev/app/acme/TASK-7');
  const bodies = await Promise.all(
    supabase.sent
      .filter((each) => new URL(each.url).pathname.includes('/rpc/'))
      .map(async (each) => [new URL(each.url).pathname.split('/').at(-1), await each.json()]),
  );
  expect(bodies).toEqual([
    [
      'create_task',
      { spec: 's1', title: 'Test the retry job', role: 'test', body: '', criteria: [1] },
    ],
    ['update_task', { task: 't1', status: 'in_progress' }],
    [
      'update_task',
      {
        task: 't1',
        status: 'in_review',
        pull_request: 'https://github.com/acme-co/payments/pull/12',
      },
    ],
  ]);
});

test('an agent can’t ask to mark a task done', async () => {
  const { text, isError } = await tool('update_task', {
    workspace: 'acme',
    task: 'TASK-7',
    status: 'done',
  });
  expect(isError).toBe(true);
  expect(text).toMatch(/status/);
});

test('a criterion ID that isn’t one is answered with what one looks like', async () => {
  const { text, isError } = await tool('reword_criterion', {
    workspace: 'acme',
    criterion: 'AC-2',
    text: 'x',
  });
  expect(isError).toBe(true);
  expect(text).toBe('AC-2 isn’t a criterion’s ID. One looks like SPEC-12/AC-3.');
});

test('Postgres’s refusal comes back in its words', async () => {
  const supabase = standIn({
    refuse: {
      code: '42501',
      message: 'An agent can’t remove a criterion. A person does that in Sulba',
    },
  });
  const { text, isError } = await tool(
    'update_spec',
    { workspace: 'acme', spec: 'SPEC-3', status: 'implemented' },
    supabase.fetch,
  );
  expect(isError).toBe(true);
  expect(text).toBe('An agent can’t remove a criterion. A person does that in Sulba.');
});

test('an agent can’t ask to approve a spec', async () => {
  const { isError, text } = await tool('update_spec', {
    workspace: 'acme',
    spec: 'SPEC-3',
    status: 'approved',
  });
  expect(isError).toBe(true);
  expect(text).toContain('expected one of "draft"|"in_review"|"implemented"');
});

test('a criterion’s proof reads as a phrase', () => {
  const base = {
    criterionId: 'c',
    specId: 's',
    specNumber: 1,
    specTitle: 'T',
    specStatus: 'approved',
    criterionNumber: 1,
    text: 't',
    checkedAt: null,
  } as const;
  expect(proofText(undefined)).toBe('Unproven: no test names it yet');
  expect(
    proofText({
      ...base,
      state: 'proven',
      tests: 1,
      passed: 1,
      failed: 0,
      skipped: 0,
      suspectSince: null,
    }),
  ).toBe('Proven by 1 test');
  expect(
    proofText({
      ...base,
      state: 'unproven',
      tests: 2,
      passed: 0,
      failed: 0,
      skipped: 2,
      suspectSince: null,
    }),
  ).toBe('Unproven: 2 tests were skipped');
  expect(
    proofText({
      ...base,
      state: 'unproven',
      tests: 1,
      passed: 1,
      failed: 0,
      skipped: 0,
      suspectSince: '2026-10-28T00:00:00Z',
    }),
  ).toBe(
    'Unproven: reworded since its tests ran, until a person confirms they check the new wording',
  );
});
