/*
  Takes a test report from a team's CI (decision record 50). A step in a GitHub Actions job asks
  GitHub for the run's OpenID Connect token, made out to sulba.dev, and sends it with the run's
  JUnit XML. The token is checked against GitHub's published keys, so no secret sits in the team's
  repository, and its claims say which repository, branch, commit and run the report is from.
  Postgres reads the report itself (record_report), which keeps the Worker's work to the token.
  The settings, keys and fetch are passed in, so the steps can be tested without the network.
*/
import { createRemoteJWKSet, type JWTPayload, type JWTVerifyGetKey, jwtVerify } from 'jose';

export const issuer = 'https://token.actions.githubusercontent.com';
export const audience = 'https://sulba.dev';
/** GitHub's keys, which jose fetches once and keeps. */
export const githubKeys = createRemoteJWKSet(new URL(`${issuer}/.well-known/jwks`));
/** The most a request's report can hold, well under what the Worker accepts. */
export const MAX_BYTES = 10 * 1024 * 1024;

const TIMEOUT = 20_000;
const claimNames = [
  'repository',
  'repository_id',
  'repository_owner_id',
  'ref',
  'sha',
  'run_id',
  'run_attempt',
  'workflow',
] as const;

export type Run = Record<(typeof claimNames)[number], string>;

export interface Settings {
  /** Supabase's secret key, a Worker secret. Without it no report is taken. */
  secretKey: string | undefined;
  supabaseUrl: string;
  keys: JWTVerifyGetKey;
}

/** What record_report says it kept. */
export interface Kept {
  kept: boolean;
  branch: string;
  tests?: number;
  passed?: number;
  failed?: number;
  skipped?: number;
  criteria?: { spec: number; criterion: number; outcome: string; known: boolean }[];
}

const answer = (status: number, ...lines: string[]) =>
  new Response(`${lines.join('\n')}\n`, {
    status,
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });

/** The run the token describes, or undefined when it lacks a claim a report needs. */
export function runOf(payload: JWTPayload): Run | undefined {
  const run: Partial<Run> = {};
  for (const name of claimNames) {
    const value = payload[name];
    if (typeof value !== 'string' || value === '') return undefined;
    run[name] = value;
  }
  return run as Run;
}

/** The report's XML documents: the body itself, or each `report` part of a form. */
async function reportsIn(request: Request): Promise<string[]> {
  if (request.headers.get('Content-Type')?.startsWith('multipart/form-data')) {
    const form = await request.formData();
    return Promise.all(
      form.getAll('report').map((part) => (typeof part === 'string' ? part : part.text())),
    );
  }
  const text = await request.text();
  return text.trim() === '' ? [] : [text];
}

/** What the run's log says about what Sulba kept. */
export function said(kept: Kept, run: Run, suite: string, evidence: string): string[] {
  const repository = run.repository;
  if (!kept.kept) {
    return [
      `Sulba keeps reports from ${repository}’s ${kept.branch} branch, and this run is on ${run.ref}, so it kept nothing.`,
    ];
  }
  const count = (n: number | undefined, one: string, many: string) =>
    `${(n ?? 0).toLocaleString('en-GB')} ${n === 1 ? one : many}`;
  const lines = [
    `Sulba kept ${count(kept.tests, 'test', 'tests')} from ${repository} at ${run.sha.slice(0, 7)} (suite ${suite}): ${kept.passed ?? 0} passed, ${kept.failed ?? 0} failed, ${kept.skipped ?? 0} skipped.`,
  ];
  const criteria = kept.criteria ?? [];
  if (criteria.length === 0) {
    lines.push(
      'None of them names a criterion. A test claims one by putting its ID in its name, such as test_SPEC_1_AC_1_retries.',
    );
  } else {
    lines.push(`They name ${count(criteria.length, 'criterion', 'criteria')}:`);
    for (const each of criteria) {
      const id = `SPEC-${each.spec}/AC-${each.criterion}`;
      lines.push(`  ${id} ${each.outcome}${each.known ? '' : `, but this workspace has no ${id}`}`);
    }
  }
  lines.push(`See them at ${evidence}`);
  return lines;
}

/** The status for each refusal record_report raises. */
const refusals: Record<string, number> = { P0002: 404, '42501': 403, '22023': 400, '54000': 429 };

export async function receive(
  request: Request,
  settings: Settings,
  network: { fetch: typeof fetch },
): Promise<Response> {
  if (!settings.secretKey) {
    return answer(503, 'Sulba can’t take test reports right now. The run can go on without it.');
  }
  const url = new URL(request.url);
  const workspace = url.searchParams.get('workspace') ?? '';
  const suite = url.searchParams.get('suite') || 'tests';
  if (!/^[a-z0-9-]{3,32}$/.test(workspace)) {
    return answer(400, 'Name the workspace in the address: ?workspace=<its address in Sulba>.');
  }
  if (!/^[A-Za-z0-9_.-]{1,64}$/.test(suite)) {
    return answer(
      400,
      'A suite’s name has at most 64 letters, digits, dots, hyphens and underscores.',
    );
  }

  const token = /^Bearer (\S+)$/.exec(request.headers.get('Authorization') ?? '')?.[1];
  if (!token) {
    return answer(
      401,
      'Send the run’s OpenID Connect token as Authorization: Bearer <token>. The job needs the id-token: write permission.',
    );
  }
  let run: Run | undefined;
  try {
    const { payload } = await jwtVerify(token, settings.keys, {
      issuer,
      audience,
      algorithms: ['RS256'],
    });
    run = runOf(payload);
  } catch {
    run = undefined;
  }
  if (!run) {
    return answer(
      401,
      `The token isn’t one GitHub Actions made out to ${audience}, or it has expired. Ask for it with audience=${audience}.`,
    );
  }

  if (Number(request.headers.get('Content-Length') ?? 0) > MAX_BYTES) {
    return answer(413, 'A report can be at most 10 MB.');
  }
  let reports: string[];
  try {
    reports = await reportsIn(request);
  } catch {
    return answer(400, 'The report couldn’t be read.');
  }
  if (reports.reduce((total, each) => total + each.length, 0) > MAX_BYTES) {
    return answer(413, 'A report can be at most 10 MB.');
  }
  if (reports.length === 0) {
    return answer(400, 'Send the JUnit XML report as the request’s body.');
  }

  let response: Response;
  try {
    response = await network.fetch(`${settings.supabaseUrl}/rest/v1/rpc/record_report`, {
      method: 'POST',
      headers: { apikey: settings.secretKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace, suite, run, reports }),
      signal: AbortSignal.timeout(TIMEOUT),
    });
  } catch {
    return answer(502, 'Sulba couldn’t record the report. Run the job again to send it again.');
  }
  if (!response.ok) {
    const refusal = (await response.json().catch(() => ({}))) as {
      code?: string;
      message?: string;
    };
    const status = refusals[refusal.code ?? ''];
    return status && refusal.message
      ? answer(status, /[.!?]$/.test(refusal.message) ? refusal.message : `${refusal.message}.`)
      : answer(502, 'Sulba couldn’t record the report. Run the job again to send it again.');
  }
  const kept = (await response.json()) as Kept;
  return answer(200, ...said(kept, run, suite, `${url.origin}/app/${workspace}/evidence`));
}
