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
}: {
  refuse?: { code: string; message: string };
  disconnected?: boolean;
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
      const row = { role: 'member', workspaces: workspace };
      return json(one ? row : [row]);
    }
    if (path.endsWith('/specs')) return json(one ? spec : [spec]);
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
    'get_evidence',
  ]);
  expect(
    list.result.tools.filter((each) => each.annotations.readOnlyHint).map((each) => each.name),
  ).toEqual(['list_workspaces', 'list_specs', 'get_spec', 'get_evidence']);
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
