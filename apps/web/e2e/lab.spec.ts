import { expect, type Page, test } from '@playwright/test';

// The tests build the site from the content package's fixture course (playwright.config.ts): a lab
// of two stages on tally.py, whose tests read a small CSV of votes.
const path = '/demo/counting/tallies/';

const solved = {
  count: 'def count(choices, choice):\n    return sum(1 for each in choices if each == choice)\n',
};

async function openLab(page: Page, query = '') {
  await page.goto(`${path}${query}`);
  await expect(code(page)).toBeVisible();
}

function code(page: Page) {
  return page.getByRole('textbox', { name: 'tally.py', exact: true });
}

/** Replaces the learner's code, as a paste would. */
async function write(page: Page, text: string) {
  await code(page).fill(text);
}

async function runTests(page: Page) {
  await page.getByRole('button', { name: 'Run tests' }).click();
}

const summary = (page: Page) =>
  page.getByText(/tests pass\.|test (passes|fails)\.|couldn’t run|were stopped/);

// A page's first run waits for Python to load, which takes longer while other tests load it too.
const loaded = { timeout: 60_000 };

test('a run lists each test, with the error and the line it came from', async ({ page }) => {
  await openLab(page);

  await runTests(page);

  await expect(summary(page)).toHaveText('0 of 2 tests pass.', loaded);
  const first = page.getByRole('listitem').filter({ hasText: 'Two votes for yes' });
  await expect(first).toContainText('NotImplementedError');
  await first.getByRole('button', { name: 'tally.py, line 3' }).click();
  await expect(code(page)).toBeFocused();
});

test('passing every test finishes the stage, and the next builds on the learner’s code', async ({
  page,
}) => {
  await openLab(page);
  await expect(page.getByRole('button', { name: /Share/ })).toBeDisabled();

  await write(page, solved.count);
  await runTests(page);
  await expect(summary(page)).toHaveText('All 2 tests pass.', loaded);
  await expect(page.getByText('Stage 1 done.')).toBeVisible();
  await page.getByRole('button', { name: 'Next stage' }).click();

  await expect(page).toHaveURL(/\?stage=share$/);
  await expect(code(page)).toContainText('return sum(1 for each in choices if each == choice)');
  await expect(code(page)).toContainText('def share(choices, choice):');
  await runTests(page);
  await expect(summary(page)).toHaveText('The test fails.', loaded);
});

test('the solution opens after the first run', async ({ page }) => {
  await openLab(page);
  const solution = page.getByRole('tab', { name: 'Solution' });
  await expect(solution).toHaveAttribute('aria-disabled', 'true');

  await runTests(page);
  await expect(summary(page)).toBeVisible(loaded);
  await solution.click();

  await expect(page.getByRole('textbox', { name: 'Solution: tally.py' })).toContainText(
    'return sum(1 for each in choices if each == choice)',
  );
});

test('the explanation shows its formulas, with the numbers its figures.py computes', async ({
  page,
}) => {
  await openLab(page);

  await page.getByRole('tab', { name: 'Explanation' }).click();

  const panel = page.getByRole('tabpanel', { name: 'Explanation' });
  await expect(panel.locator('math[display="block"]')).toContainText('count');
  await expect(panel.locator('math[display="block"] munderover')).toContainText('∑');
  await expect(panel).toContainText('The poll has 3 votes');
  await expect(panel.locator('math').last()).toContainText('2');
});

test('hints open one at a time', async ({ page }) => {
  await openLab(page);
  await page.getByRole('tab', { name: 'Hints' }).click();

  await page.getByRole('button', { name: 'Show a hint' }).click();
  await expect(page.getByText('Compare each choice with the one you are counting.')).toBeVisible();
  await expect(page.getByText('adds up a generator of ones')).toBeHidden();
  await page.getByRole('button', { name: 'Show the next hint' }).click();

  await expect(page.getByText('adds up a generator of ones')).toBeVisible();
  await expect(page.getByText('That’s every hint for this stage.')).toBeVisible();
});

test('the code is kept when the page reloads, and Reset brings back the starter', async ({
  page,
}) => {
  await openLab(page);
  await write(page, 'def count(choices, choice):\n    return 7\n');

  await page.reload();
  await expect(code(page)).toContainText('return 7');
  await page.getByRole('button', { name: 'Reset' }).click();

  await expect(code(page)).toContainText('raise NotImplementedError');
  await page.reload();
  await expect(code(page)).toContainText('raise NotImplementedError');
});

test('a syntax error stops the run and points to its line', async ({ page }) => {
  await openLab(page);
  await write(page, 'def count(choices, choice:\n    return 0\n');

  await runTests(page);

  await expect(summary(page)).toHaveText('The tests couldn’t run: your code has an error.', loaded);
  await expect(page.getByText(/^SyntaxError: /)).toBeVisible();
  await expect(page.getByRole('button', { name: 'tally.py, line 1' })).toBeVisible();
});

test('a loop that never ends is stopped, and the next run works', async ({ page }) => {
  await openLab(page);
  await write(page, 'def count(choices, choice):\n    while True:\n        pass\n');

  await runTests(page);
  await expect(summary(page)).toHaveText(
    'The tests were stopped after 5 seconds. A loop that never ends is the usual cause.',
    loaded,
  );
  await write(page, solved.count);
  await runTests(page);

  await expect(summary(page)).toHaveText('All 2 tests pass.', loaded);
});

test('a stage the address names opens only once the stage before is done', async ({ page }) => {
  await openLab(page, '?stage=share');
  await expect(page.getByRole('heading', { name: 'Count' })).toBeVisible();

  await write(page, solved.count);
  await runTests(page);
  await expect(summary(page)).toHaveText('All 2 tests pass.', loaded);
  await openLab(page, '?stage=share');

  await expect(page.getByRole('heading', { name: 'Share' })).toBeVisible();
});

test('the lab page fits the screen without scrolling sideways', async ({ page }) => {
  await openLab(page);
  const width = await page.evaluate(() => document.documentElement.scrollWidth);

  expect(width).toBeLessThanOrEqual(page.viewportSize()?.width ?? 0);
});
