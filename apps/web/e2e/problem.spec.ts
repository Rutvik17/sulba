import { expect, type Page, test } from '@playwright/test';
import { write } from './editor';

// The tests build the site from the content package's fixture course (playwright.config.ts), whose
// module Interviews has the lab Pairs: one Problem stage, with 20 minutes to write pair_sum.
const path = '/demo/interviews/pairs/';

const solution = [
  'def pair_sum(numbers, target):',
  '    seen = {}',
  '    for position, number in enumerate(numbers):',
  '        partner = seen.get(target - number)',
  '        if partner is not None:',
  '            return (partner, position)',
  '        seen.setdefault(number, position)',
  '    return None',
  '',
].join('\n');

/** Keeps the problem as started this many seconds before the page first opens, its plan written. */
async function startedAgo(page: Page, seconds: number) {
  await page.addInitScript((ago) => {
    const key = 'sulba:problem:stg_demo05';
    // The script runs on every load, so a reload finds what the page has kept since.
    if (localStorage.getItem(key) !== null) return;
    const state = { started: Date.now() - ago * 1000, plan: 'A dict of the numbers seen.' };
    localStorage.setItem(key, JSON.stringify({ ...state, coding: true, solved: null }));
  }, seconds);
}

const code = (page: Page) => page.getByRole('textbox', { name: 'pairs.py', exact: true });
const timer = (page: Page) => page.getByRole('timer');
const plan = (page: Page) => page.getByRole('textbox', { name: 'Your plan' });

// A page's first run waits for Python to load, which takes longer while other tests load it too.
const loaded = { timeout: 60_000 };
test.describe.configure({ timeout: 90_000 });

test('a problem shows once it starts, and its code once the plan is written', async ({ page }) => {
  await page.goto(path);
  const start = page.getByRole('button', { name: 'Start' });
  await expect(start).toBeVisible();
  await expect(page.getByText('Write pair_sum')).toBeHidden();
  await expect(page.getByRole('button', { name: 'Run tests' })).toBeDisabled();
  await expect(timer(page)).toBeHidden();

  await start.click();

  // The problem takes the focus, so it's what the learner reads first.
  await expect(page.locator(':focus')).toContainText('Write pair_sum');
  await expect(timer(page)).toHaveText(/^0:0\d of 20:00$/);
  const done = page.getByRole('button', { name: 'Write the code' });
  await expect(done).toBeDisabled();
  await plan(page).fill('A dict from each number seen to its position, in one pass.');
  await done.click();

  await expect(code(page)).toBeFocused();
  await expect(page.getByRole('button', { name: 'Run tests' })).toBeEnabled();
  await page.getByRole('tab', { name: 'Plan', exact: true }).click();
  await expect(plan(page)).toHaveValue(
    'A dict from each number seen to its position, in one pass.',
  );

  // The start and the plan are kept: the code opens again on a reload, and the clock runs on.
  await page.reload();
  await expect(code(page)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Start' })).toBeHidden();
  await expect(timer(page)).toHaveText(/^0:\d\d of 20:00$/);
});

test('solving a problem stops its clock, and says how its time compares with its minutes', async ({
  page,
}) => {
  await page.clock.install();
  await startedAgo(page, 3 * 60);
  await page.goto(path);
  await expect(timer(page)).toHaveText(/^3:0\d of 20:00$/);
  await expect(page.getByRole('tab', { name: 'Solution' })).toHaveAttribute(
    'aria-disabled',
    'true',
  );

  await write(code(page), solution);
  await page.getByRole('button', { name: 'Run tests' }).click();

  await expect(page.getByText('All 3 tests passed.')).toBeVisible(loaded);
  await expect(page.getByText(/^Solved in 3:\d\d, inside its 20 minutes\.$/)).toBeVisible();
  const solved = (await timer(page).textContent()) ?? '';
  expect(solved).toMatch(/^3:\d\d of 20:00$/);
  // The clock stays at the time of the run that passed, then and after a reload.
  await page.clock.fastForward('00:10');
  await expect(timer(page)).toHaveText(solved);
  await page.getByRole('tab', { name: 'Explanation' }).click();
  await expect(page.getByText('One pass with a dict')).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Solution' })).not.toHaveAttribute(
    'aria-disabled',
    'true',
  );

  await page.reload();
  await expect(code(page)).toBeVisible();
  await expect(timer(page)).toHaveText(solved);
  await expect(page.getByRole('button', { name: /Pair sums/ })).toContainText('Done');
});

test('a problem solved on another device opens in full, with no clock', async ({ page }) => {
  await startedAgo(page, 30 * 60);
  await page.addInitScript(() => localStorage.setItem('sulba:passed:stg_demo05', '1'));
  await page.goto(path);

  await expect(code(page)).toBeVisible();
  await expect(timer(page)).toBeHidden();
  await expect(page.getByRole('tab', { name: 'Solution' })).not.toHaveAttribute(
    'aria-disabled',
    'true',
  );
});

test("a problem's explanation and solution open once its minutes are up", async ({ page }) => {
  await page.clock.install();
  await startedAgo(page, 20 * 60 - 30);
  await page.goto(path);
  await expect(timer(page)).toHaveText(/^19:3\d of 20:00$/);
  await page.getByRole('tab', { name: 'Explanation' }).click();
  const explanation = page.getByRole('tabpanel', { name: 'Explanation' });
  await expect(explanation).toHaveText('Opens when you solve it, or when its 20 minutes are up.');
  const solution = page.getByRole('tab', { name: 'Solution' });
  await expect(solution).toHaveAttribute('aria-disabled', 'true');

  await page.clock.fastForward('01:00');

  await expect(timer(page)).toHaveText(/^20:3\d of 20:00$/);
  await expect(explanation).toContainText('One pass with a dict');
  await expect(solution).not.toHaveAttribute('aria-disabled', 'true');
});
