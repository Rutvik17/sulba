import type { Page } from '@playwright/test';

// The hosted project, which the site's build points at. Tests stand in for every request to it,
// and refuse any they don't expect, so no test ever reaches the real project.
export const supabase = 'https://cqsfhuxtpkzvlemqkqoa.supabase.co';

export const learner = { id: 'a0000000-0000-4000-8000-000000000001', email: 'ada@example.com' };

const cors = {
  'access-control-allow-origin': '*',
  'access-control-allow-headers': '*',
  'access-control-allow-methods': 'GET, POST, PATCH, DELETE, OPTIONS',
};

function base64url(value: object): string {
  return Buffer.from(JSON.stringify(value)).toString('base64url');
}

/** A session as Supabase hands one out, for an hour from now. */
export function session() {
  const expires = Math.floor(Date.now() / 1000) + 3600;
  const claims = { sub: learner.id, role: 'authenticated', aud: 'authenticated', exp: expires };
  return {
    access_token: `${base64url({ alg: 'HS256', typ: 'JWT' })}.${base64url(claims)}.signature`,
    token_type: 'bearer',
    expires_in: 3600,
    expires_at: expires,
    refresh_token: 'refresh-token',
    user: {
      id: learner.id,
      aud: 'authenticated',
      role: 'authenticated',
      email: learner.email,
      app_metadata: { provider: 'github', providers: ['github'] },
      user_metadata: {},
      created_at: '2026-10-14T10:00:00Z',
    },
  };
}

/** What the page sent to the stand-in. */
export interface Calls {
  readonly authorize: URL[];
  readonly attempts: Record<string, unknown>[];
  logouts: number;
  closed: number;
}

/** What the stand-in account holds. */
export interface Held {
  /** A progress row for each stage passed. */
  readonly passed?: { stage_id: string; caught: string[] | null; problems: number | null }[];
  /** A study_days row for each day studied. */
  readonly studyDays?: { day: string; seconds: number }[];
}

/**
 * Stands in for Supabase: sign-in hands back a code, the code a session, and the account holds the
 * rows given.
 */
export async function standIn(
  page: Page,
  { passed = [], studyDays = [] }: Held = {},
): Promise<Calls> {
  const calls: Calls = { authorize: [], attempts: [], logouts: 0, closed: 0 };
  const answer = (status: number, body?: unknown) => ({
    status,
    headers: { ...cors, 'content-type': 'application/json' },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });

  await page.route(`${supabase}/**`, (route) => route.abort());
  await page.route(`${supabase}/auth/v1/authorize**`, (route) => {
    calls.authorize.push(new URL(route.request().url()));
    const back = new URL(calls.authorize.at(-1)?.searchParams.get('redirect_to') ?? '/');
    back.searchParams.set('code', 'code-from-github');
    return route.fulfill({ status: 302, headers: { location: back.href } });
  });
  await page.route(`${supabase}/auth/v1/token**`, (route) =>
    route.request().method() === 'OPTIONS'
      ? route.fulfill(answer(204))
      : route.fulfill(answer(200, session())),
  );
  await page.route(`${supabase}/auth/v1/logout**`, (route) => {
    if (route.request().method() !== 'OPTIONS') calls.logouts++;
    return route.fulfill(answer(204));
  });
  await page.route(`${supabase}/rest/v1/progress**`, (route) =>
    route.request().method() === 'OPTIONS'
      ? route.fulfill(answer(204))
      : route.fulfill(answer(200, passed)),
  );
  await page.route(`${supabase}/rest/v1/study_days**`, (route) =>
    route.request().method() === 'OPTIONS'
      ? route.fulfill(answer(204))
      : route.fulfill(answer(200, studyDays)),
  );
  await page.route(`${supabase}/rest/v1/attempts**`, (route) => {
    if (route.request().method() === 'OPTIONS') return route.fulfill(answer(204));
    calls.attempts.push(...(route.request().postDataJSON() as Record<string, unknown>[]));
    return route.fulfill(answer(201));
  });
  await page.route(`${supabase}/rest/v1/rpc/close_account**`, (route) => {
    if (route.request().method() !== 'OPTIONS') calls.closed++;
    return route.fulfill(answer(204));
  });
  return calls;
}

/** Opens the page with a session already in this browser, as after signing in. */
export async function signedIn(page: Page) {
  await page.addInitScript((value) => {
    localStorage.setItem('sulba:session', value);
  }, JSON.stringify(session()));
}
