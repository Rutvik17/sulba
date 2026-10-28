import { createLocalJWKSet, exportJWK, generateKeyPair, type JWTPayload, SignJWT } from 'jose';
import { beforeAll, expect, test, vi } from 'vitest';
import { audience, issuer, MAX_BYTES, receive, type Settings } from './results';

// A key that stands in for GitHub's, and a run's claims as GitHub Actions gives them.
const pair = await generateKeyPair('RS256');
let settings: Settings;
beforeAll(async () => {
  const key = { ...(await exportJWK(pair.publicKey)), kid: 'github', alg: 'RS256' };
  settings = {
    secretKey: 'sb_secret_test',
    supabaseUrl: 'https://project.supabase.co',
    keys: createLocalJWKSet({ keys: [key] }),
  };
});

const claims = {
  repository: 'acme-co/payments',
  repository_id: '101',
  repository_owner_id: '55',
  ref: 'refs/heads/main',
  sha: 'a1b2c3d4e5f60718293a4b5c6d7e8f9012345678',
  run_id: '1000',
  run_attempt: '1',
  workflow: 'CI',
};

function token(
  payload: JWTPayload = claims,
  { to = audience, from = issuer, expires = '5m' } = {},
) {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: 'RS256', kid: 'github' })
    .setIssuer(from)
    .setAudience(to)
    .setIssuedAt()
    .setExpirationTime(expires)
    .sign(pair.privateKey);
}

const report =
  '<testsuites><testsuite><testcase name="test_SPEC_1_AC_1_retries"/></testsuite></testsuites>';

async function request({
  query = '?workspace=acme&suite=unit',
  bearer,
  body = report as BodyInit,
  type = 'application/xml',
}: {
  query?: string;
  bearer?: string | null;
  body?: BodyInit;
  type?: string | null;
} = {}) {
  const headers = new Headers();
  const given = bearer === undefined ? await token() : bearer;
  if (given) headers.set('Authorization', `Bearer ${given}`);
  if (type) headers.set('Content-Type', type);
  return new Request(`https://sulba.dev/api/results${query}`, { method: 'POST', headers, body });
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

/** A stand-in for Supabase, which answers record_report with the given response. */
function supabase(
  answer: Response | Error = json({
    kept: true,
    branch: 'main',
    tests: 0,
    passed: 0,
    failed: 0,
    skipped: 0,
    criteria: [],
  }),
) {
  return vi.fn<typeof fetch>(async () => {
    if (answer instanceof Error) throw answer;
    return answer;
  });
}

test('a report goes to record_report with the run the token describes, on the secret key', async () => {
  const fetch = supabase(
    json({
      kept: true,
      branch: 'main',
      tests: 412,
      passed: 401,
      failed: 3,
      skipped: 8,
      criteria: [
        { spec: 1, criterion: 1, outcome: 'passed', known: true },
        { spec: 9, criterion: 1, outcome: 'failed', known: false },
      ],
    }),
  );

  const response = await receive(await request(), settings, { fetch });

  expect(response.status).toBe(200);
  expect(await response.text()).toBe(
    [
      'Sulba kept 412 tests from acme-co/payments at a1b2c3d (suite unit): 401 passed, 3 failed, 8 skipped.',
      'They name 2 criteria:',
      '  SPEC-1/AC-1 passed',
      '  SPEC-9/AC-1 failed, but this workspace has no SPEC-9/AC-1',
      'See them at https://sulba.dev/app/acme/evidence',
      '',
    ].join('\n'),
  );
  const [url, init] = fetch.mock.calls[0] ?? [];
  expect(url).toBe('https://project.supabase.co/rest/v1/rpc/record_report');
  expect(new Headers(init?.headers).get('apikey')).toBe('sb_secret_test');
  expect(JSON.parse(String(init?.body))).toEqual({
    workspace: 'acme',
    suite: 'unit',
    run: claims,
    reports: [report],
  });
});

test('a report from another branch is answered, and says so', async () => {
  const fetch = supabase(json({ kept: false, branch: 'main' }));
  const response = await receive(
    await request({ bearer: await token({ ...claims, ref: 'refs/pull/7/merge' }) }),
    settings,
    { fetch },
  );

  expect(response.status).toBe(200);
  expect(await response.text()).toBe(
    'Sulba keeps reports from acme-co/payments’s main branch, and this run is on refs/pull/7/merge, so it kept nothing.\n',
  );
});

test('a report that names no criterion says how a test claims one', async () => {
  const response = await receive(await request({ query: '?workspace=acme' }), settings, {
    fetch: supabase(),
  });

  const text = await response.text();
  expect(text).toContain('(suite tests)');
  expect(text).toContain('None of them names a criterion.');
});

test('the files of a form go as one report', async () => {
  const form = new FormData();
  form.append('report', new Blob(['<testsuite name="a"/>']), 'TEST-a.xml');
  form.append('report', new Blob(['<testsuite name="b"/>']), 'TEST-b.xml');
  const fetch = supabase();

  await receive(await request({ body: form, type: null }), settings, { fetch });

  expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body)).reports).toEqual([
    '<testsuite name="a"/>',
    '<testsuite name="b"/>',
  ]);
});

test('without the secret key, nothing is taken', async () => {
  const fetch = supabase();
  const response = await receive(await request(), { ...settings, secretKey: undefined }, { fetch });

  expect(response.status).toBe(503);
  expect(fetch).not.toHaveBeenCalled();
});

test('a token GitHub didn’t make out to Sulba, or that has expired, is refused', async () => {
  const fetch = supabase();
  const other = await generateKeyPair('RS256');
  const forged = await new SignJWT(claims)
    .setProtectedHeader({ alg: 'RS256', kid: 'github' })
    .setIssuer(issuer)
    .setAudience(audience)
    .setExpirationTime('5m')
    .sign(other.privateKey);

  for (const bearer of [
    null,
    'not-a-token',
    forged,
    await token(claims, { to: 'https://github.com/acme-co' }),
    await token(claims, { from: 'https://example.com' }),
    await token(claims, { expires: '-1m' }),
    await token({ ...claims, repository_id: undefined }),
  ]) {
    const response = await receive(await request({ bearer }), settings, { fetch });
    expect(response.status).toBe(401);
  }
  expect(fetch).not.toHaveBeenCalled();
});

test('the address names a workspace and, if it likes, a suite', async () => {
  const fetch = supabase();
  for (const query of ['', '?workspace=A', '?workspace=acme&suite=has%20spaces']) {
    const response = await receive(await request({ query }), settings, { fetch });
    expect(response.status).toBe(400);
  }
  expect(fetch).not.toHaveBeenCalled();
});

test('an empty or too large report is refused before it goes anywhere', async () => {
  const fetch = supabase();

  expect((await receive(await request({ body: ' ' }), settings, { fetch })).status).toBe(400);
  expect(
    (await receive(await request({ body: 'x'.repeat(MAX_BYTES + 1) }), settings, { fetch })).status,
  ).toBe(413);
  expect(fetch).not.toHaveBeenCalled();
});

test('a refusal from Postgres reaches the run’s log in its own words', async () => {
  const cases = [
    { code: 'P0002', status: 404 },
    { code: '42501', status: 403 },
    { code: '22023', status: 400 },
    { code: '54000', status: 429 },
  ];
  for (const { code, status } of cases) {
    const fetch = supabase(json({ code, message: 'What Postgres said' }, 400));
    const response = await receive(await request(), settings, { fetch });
    expect(response.status).toBe(status);
    expect(await response.text()).toBe('What Postgres said.\n');
  }
});

test('anything else is a failure to try again', async () => {
  for (const answer of [json({ code: 'XX000', message: 'internal' }, 500), new Error('offline')]) {
    const response = await receive(await request(), settings, { fetch: supabase(answer) });
    expect(response.status).toBe(502);
    expect(await response.text()).toContain('Run the job again');
  }
});
