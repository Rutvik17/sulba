import { expect, test } from '@playwright/test';
import { write } from './editor';
import { islandsHydrated } from './islands';
import { learner, signedIn, standIn, supabase } from './supabase';

// The content package's fixture course: its lab's first two stages build tally.py.
const lab = '/demo/counting/tallies/';
const solved =
  'def count(choices, choice):\n    return sum(1 for each in choices if each == choice)\n';

// Days studied, as study_days holds them: three in a row up to 14 October 2026, and one before.
const studyDays = [
  { day: '2026-10-01', seconds: 1500 },
  { day: '2026-10-12', seconds: 600 },
  { day: '2026-10-13', seconds: 3900 },
  { day: '2026-10-14', seconds: 300 },
];

// A page's first run waits for Python to load, which takes longer while other tests load it too.
const loaded = { timeout: 60_000 };
test.describe.configure({ timeout: 90_000 });

test('signed out, the top bar offers sign-in, and no page loads anything from Supabase', async ({
  page,
}) => {
  const origins = new Set<string>();
  page.on('request', (request) => origins.add(new URL(request.url()).origin));

  await page.goto('/about/', { waitUntil: 'networkidle' });
  await expect(page.getByRole('link', { name: 'Sign in' })).toHaveAttribute(
    'href',
    '/sign-in/?next=%2Fabout%2F',
  );
  await expect(page.getByRole('link', { name: 'Account' })).toBeHidden();
  await page.goto(lab, { waitUntil: 'networkidle' });

  expect(origins.has(supabase)).toBe(false);
});

test('signing in with GitHub uses PKCE, and brings the learner back to where they started', async ({
  page,
}) => {
  const calls = await standIn(page);
  await page.goto('/about/');
  await page.getByRole('link', { name: 'Sign in' }).click();

  await page.getByRole('button', { name: 'Continue with GitHub' }).click();

  await expect(page).toHaveURL(/\/about\/$/);
  await expect(page.getByRole('link', { name: 'Account' })).toBeVisible();
  const authorize = calls.authorize[0];
  expect(authorize?.searchParams.get('provider')).toBe('github');
  expect(authorize?.searchParams.get('redirect_to')).toBe(new URL('/sign-in/', page.url()).href);
  expect(authorize?.searchParams.get('code_challenge_method')).toBe('s256');
});

test('a sign-in that was cancelled says so', async ({ page }) => {
  await standIn(page);
  await page.goto('/sign-in/?error=access_denied&error_description=Cancelled');
  await expect(page.getByRole('status')).toHaveText("Sign-in didn't finish. Try again.");
});

test('the account page shows who is signed in, and signs them out', async ({ page }) => {
  const calls = await standIn(page);
  await signedIn(page);
  await page.goto('/account/');

  await expect(page.getByText(`Signed in as ${learner.email} with GitHub.`)).toBeVisible();
  await page.getByRole('button', { name: 'Sign out' }).click();

  await expect(page.getByRole('status')).toHaveText('You signed out of this browser.');
  await expect(page.getByText("You're not signed in.")).toBeVisible();
  await expect(page.getByRole('link', { name: 'Sign in' }).first()).toBeVisible();
  expect(calls.logouts).toBe(1);
});

test('the account page shows the streak, and the days it comes from', async ({ page }) => {
  await page.clock.setFixedTime(new Date('2026-10-14T12:00:00'));
  await standIn(page, { studyDays });
  await signedIn(page);
  await page.goto('/account/');

  await expect(page.locator('.streak')).toHaveText('3 days in a row, up to today');
  await expect(page.getByText('You studied on 4 of the last 84 days.')).toBeVisible();
  await expect(page.locator('.day[data-studied="streak"]')).toHaveCount(3);
  await expect(page.locator('.day[data-studied=""]')).toHaveCount(1);
  await expect(page.locator('.day[data-today]')).toHaveAttribute(
    'title',
    'Wednesday 14 October 2026: 5 minutes',
  );
  await expect(
    page.getByRole('list', { name: 'Days studied in the last 84 days' }).getByRole('listitem'),
  ).toHaveText([
    'Thursday 1 October 2026: 25 minutes',
    'Monday 12 October 2026: 10 minutes, in your streak',
    'Tuesday 13 October 2026: 1 hour 5 minutes, in your streak',
    'Wednesday 14 October 2026: 5 minutes, in your streak',
  ]);
});

test('a streak lasts through a day not yet studied', async ({ page }) => {
  await page.clock.setFixedTime(new Date('2026-10-15T08:00:00'));
  await standIn(page, { studyDays });
  await signedIn(page);
  await page.goto('/account/');

  await expect(page.locator('.streak')).toHaveText('3 days in a row, up to yesterday');
});

test('closing an account asks first, then deletes it', async ({ page }) => {
  const calls = await standIn(page);
  await signedIn(page);
  await page.goto('/account/');

  await page.getByRole('button', { name: 'Close account' }).click();
  await expect(page.getByText('Close your account?', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Keep it' }).click();
  expect(calls.closed).toBe(0);

  await page.getByRole('button', { name: 'Close account' }).click();
  await page.getByRole('button', { name: 'Close account' }).last().click();

  await expect(page.getByRole('status')).toHaveText(
    'Your account is closed, and everything it recorded is deleted.',
  );
  expect(calls.closed).toBe(1);
});

test('signed in, a lab opens the stages passed on another device', async ({ page }) => {
  await standIn(page, { passed: [{ stage_id: 'stg_demo01', caught: null, problems: null }] });
  await signedIn(page);
  await page.goto(lab);
  await islandsHydrated(page);

  await expect(page.getByRole('button', { name: /Share/ })).toBeEnabled();
  await expect(page.getByRole('button', { name: /Count/ })).toContainText('Done');
});

test('signed in, the passes only this browser has go to the account', async ({ page }) => {
  const calls = await standIn(page);
  await signedIn(page);
  await page.addInitScript(() => localStorage.setItem('sulba:passed:stg_demo01', '1'));
  await page.goto(lab);
  await islandsHydrated(page);

  await expect
    .poll(() => calls.attempts, loaded)
    .toEqual([expect.objectContaining({ kind: 'pass', stage_id: 'stg_demo01', seconds: 0 })]);
});

test('signed in, each run and pass goes to the account, and the code never does', async ({
  page,
}) => {
  const calls = await standIn(page);
  await signedIn(page);
  await page.goto(lab);
  await islandsHydrated(page);

  const code = page.getByRole('textbox', { name: 'tally.py', exact: true });
  await write(code, solved);
  await page.getByRole('button', { name: 'Run tests' }).click();
  await expect(page.getByText('Both tests passed.')).toBeVisible(loaded);

  await expect
    .poll(() => calls.attempts.map((attempt) => attempt.kind), loaded)
    .toEqual(['run', 'pass']);
  expect(calls.attempts[0]).toMatchObject({
    stage_id: 'stg_demo01',
    tests_passed: 2,
    tests_total: 2,
    checks_total: null,
  });
  expect(JSON.stringify(calls.attempts)).not.toContain('return sum');
});
