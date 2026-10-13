import { expect, type Locator, type Page, test } from '@playwright/test';

// The tests build the site from the content package's fixture course (playwright.config.ts): a lab
// whose first two stages build tally.py, whose tests read a small CSV of votes.
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

/**
 * Replaces the code in an editor, as Select All and a paste would. Playwright's fill selects the
 * code through the browser, and on the Android phone the new code sometimes went in before the
 * editor had taken that selection in. The editor's own Select All takes effect at once.
 */
async function write(editor: Locator, text: string) {
  // The editor's shortcuts take Command on an iPhone, as on a Mac, and Control elsewhere.
  const { defaultBrowserType, isMobile } = test.info().project.use;
  await editor.press(defaultBrowserType === 'webkit' && isMobile ? 'Meta+a' : 'ControlOrMeta+a');
  await editor.page().keyboard.insertText(text);
}

async function runTests(page: Page) {
  await page.getByRole('button', { name: 'Run tests' }).click();
}

const summary = (page: Page) =>
  page.getByText(/tests pass\.|test (passes|fails)\.|couldn’t run|were stopped/);

// A page's first run waits for Python to load, which takes longer while other tests load it too.
const loaded = { timeout: 60_000 };
// So a test may take longer than Playwright's 30 seconds: the loop test loads Python twice.
test.describe.configure({ timeout: 90_000 });

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

  await write(code(page), solved.count);
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
  await write(code(page), 'def count(choices, choice):\n    return 7\n');

  await page.reload();
  await expect(code(page)).toContainText('return 7');
  await page.getByRole('button', { name: 'Reset' }).click();

  await expect(code(page)).toContainText('raise NotImplementedError');
  await page.reload();
  await expect(code(page)).toContainText('raise NotImplementedError');
});

test('a syntax error stops the run and points to its line', async ({ page }) => {
  await openLab(page);
  await write(code(page), 'def count(choices, choice:\n    return 0\n');

  await runTests(page);

  await expect(summary(page)).toHaveText('The tests couldn’t run: your code has an error.', loaded);
  await expect(page.getByText(/^SyntaxError: /)).toBeVisible();
  await expect(page.getByRole('button', { name: 'tally.py, line 1' })).toBeVisible();
});

test('a loop that never ends is stopped, and the next run works', async ({ page }) => {
  await openLab(page);
  await write(code(page), 'def count(choices, choice):\n    while True:\n        pass\n');

  await runTests(page);
  await expect(summary(page)).toHaveText(
    'The tests were stopped after 5 seconds. A loop that never ends is the usual cause.',
    loaded,
  );
  await write(code(page), solved.count);
  await runTests(page);

  await expect(summary(page)).toHaveText('All 2 tests pass.', loaded);
});

test('a stage the address names opens only once the stage before is done', async ({ page }) => {
  await openLab(page, '?stage=share');
  await expect(page.getByRole('heading', { name: 'Count' })).toBeVisible();

  await write(code(page), solved.count);
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

// The third stage is a Catch stage: an assistant's report.py, which uses the learner's share, with
// two problems its own tests miss. These tests start there, with the first two stages done.
const shareSolved = `${solved.count}\n\ndef share(choices, choice):\n    return count(choices, choice) / len(choices)\n`;

const draft = {
  /** The assistant's report.py with one problem fixed: it no longer sorts the poll's list. */
  oneFixed:
    'from tally import share\n\n\ndef report(choices):\n    return [(choice, share(choices, choice)) for choice in sorted(set(choices))]\n',
  /** Both problems fixed. */
  fixed:
    'from tally import share\n\n\ndef report(choices):\n    shares = [(choice, share(choices, choice)) for choice in set(choices)]\n    return sorted(shares, key=lambda pair: -pair[1])\n',
};

async function openReview(page: Page) {
  await page.addInitScript((code) => {
    localStorage.setItem('sulba:passed:stg_demo01', '1');
    localStorage.setItem('sulba:passed:stg_demo02', '1');
    localStorage.setItem('sulba:code:stg_demo02', code);
  }, shareSolved);
  await page.goto(`${path}?stage=check`);
  await expect(report(page)).toBeVisible();
}

function report(page: Page) {
  return page.getByRole('textbox', { name: 'report.py', exact: true });
}

/** A Catch run's summary, which leads with the production checks. */
const checked = (page: Page) => page.getByText(/production checks? (pass|passes|fails)\./);

test('a Catch stage shows the assistant’s tests, and only a count of its production checks', async ({
  page,
}) => {
  await openReview(page);
  await expect(page.getByRole('tab', { name: 'Solution' })).toHaveAttribute(
    'aria-disabled',
    'true',
  );
  await page.getByRole('tab', { name: 'Explanation' }).click();
  await expect(page.getByText('Opens when you finish the review.')).toBeVisible();

  await runTests(page);

  await expect(checked(page)).toHaveText(
    '0 of 2 production checks pass. The assistant’s tests pass.',
    loaded,
  );
  await expect(page.getByText('One line per choice')).toBeVisible();
  await expect(page.getByText('Most votes first', { exact: true })).toHaveCount(0);
  await expect(page.getByText('The fewest votes came first', { exact: true })).toHaveCount(0);
});

test('until the review is finished, a production check’s output doesn’t name the check', async ({
  page,
}) => {
  await openReview(page);
  await write(
    report(page),
    draft.oneFixed.replace('    return', '    print("reporting")\n    return'),
  );

  await runTests(page);
  await expect(checked(page)).toHaveText(
    '1 of 2 production checks pass. The assistant’s tests pass.',
    loaded,
  );
  await page.getByRole('tab', { name: 'Printed' }).click();

  const printed = page.getByRole('tabpanel', { name: 'Printed' });
  await expect(printed).toContainText('One line per choice');
  await expect(printed).toContainText('A production check');
  await expect(printed).not.toContainText('Most votes first');
});

test('finishing the review keeps the score, and names each problem with what it costs', async ({
  page,
}) => {
  await openReview(page);
  await write(report(page), draft.oneFixed);

  await page.getByRole('button', { name: 'Finish review' }).click();
  await expect(page.getByText('Finish the review?', { exact: false })).toBeVisible();
  await page
    .getByRole('tabpanel', { name: 'Tests' })
    .getByRole('button', { name: 'Finish review' })
    .click();

  await expect(page.getByText('Review finished: 1 of 2 problems caught.')).toBeFocused(loaded);
  await expect(page.getByRole('button', { name: 'Finish review' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Check/ })).toContainText('1 of 2 caught');
  await page.getByRole('button', { name: 'See each problem' }).click();
  const explanation = page.getByRole('tabpanel', { name: 'Explanation' });
  const missed = explanation
    .getByRole('listitem')
    .filter({ hasText: 'The fewest votes came first' });
  await expect(missed).toContainText('Missed');
  await expect(missed).toContainText('orders the choices by name');
  await expect(
    explanation.getByRole('listitem').filter({ hasText: "It reordered the poll's own list" }),
  ).toContainText('Caught');
  await expect(explanation).toHaveText(
    /The assistant's tests checked[\s\S]*It reordered the poll's own list[\s\S]*sorted returns a new list/,
  );
  await expect(page.getByRole('tab', { name: 'Solution' })).not.toHaveAttribute(
    'aria-disabled',
    'true',
  );

  await page.reload();
  await expect(page.getByText('Review finished: 1 of 2 problems caught.')).toBeVisible();
});

test('passing every production check finishes the review by itself', async ({ page }) => {
  await openReview(page);
  await write(report(page), draft.fixed);

  await runTests(page);

  await expect(page.getByText('Review finished: 2 of 2 problems caught.')).toBeVisible(loaded);
  await expect(
    page.getByRole('tabpanel', { name: 'Tests' }).getByRole('listitem').filter({
      hasText: 'The fewest votes came first',
    }),
  ).toContainText('✓');
});

test('Keep reviewing closes the question and goes back to Finish review', async ({ page }) => {
  await openReview(page);

  await page.getByRole('button', { name: 'Finish review' }).click();
  await page.getByRole('button', { name: 'Keep reviewing' }).click();

  await expect(page.getByText('Finish the review?', { exact: false })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Finish review' })).toBeFocused();
});

// The fourth stage is a Ship stage: leader goes below report.py, where the Catch stage's fixed code
// carries on, since its review wasn't finished. Its tests are hidden, and two checks must pass
// before it ships.
const leader = {
  /** Finds the leader, but sorts the poll's own list to do it. */
  sorting:
    'def leader(choices):\n    choices.sort()\n    return max(set(choices), key=choices.count)\n',
  fixed: 'def leader(choices):\n    return max(set(choices), key=choices.count)\n',
};

async function openShip(page: Page) {
  await page.addInitScript((code) => {
    for (const stage of ['stg_demo01', 'stg_demo02', 'stg_demo03']) {
      localStorage.setItem(`sulba:passed:${stage}`, '1');
    }
    localStorage.setItem('sulba:code:stg_demo02', code);
  }, shareSolved);
  await page.goto(`${path}?stage=ship`);
  await expect(report(page)).toBeVisible();
}

/** A check before the code ships, in the Tests tab. */
function shipCheck(page: Page, title: string) {
  return page.getByRole('tabpanel', { name: 'Tests' }).getByRole('listitem').filter({
    hasText: title,
  });
}

test('a Ship stage shows its tests by name only, what each check requires, and its explanation after a run', async ({
  page,
}) => {
  await openShip(page);
  await expect(page.getByRole('button', { name: /Leader/ })).toContainText('Ship');
  await expect(page.getByRole('tab', { name: 'Hints' })).toHaveCount(0);
  await page.getByRole('tab', { name: 'Explanation' }).click();
  const explanation = page.getByRole('tabpanel', { name: 'Explanation' });
  await expect(explanation).toHaveText('Opens after your first run.');
  const fast = shipCheck(page, 'Fast on 60,000 votes');
  await expect(fast).toContainText('leader finds the leader of 60,000 votes in under a second.');
  await expect(fast).not.toContainText('The limit is a second.');

  await runTests(page);

  await expect(summary(page)).toHaveText('0 of 2 tests pass. 0 of 2 checks pass.', loaded);
  const tests = page.getByRole('tabpanel', { name: 'Tests' });
  await expect(tests.getByRole('listitem').filter({ hasText: "The poll's leader" })).toContainText(
    '✗',
  );
  await expect(tests).not.toContainText('NotImplementedError');
  await expect(tests).not.toContainText('report.py, line');
  await expect(fast).toContainText('The limit is a second.');
  await expect(explanation).toContainText('stays fast on a long list');
  await expect(page.getByRole('tab', { name: 'Solution' })).not.toHaveAttribute(
    'aria-disabled',
    'true',
  );
});

test('a check before it ships says why it failed and what it measured, and passing every one finishes the stage', async ({
  page,
}) => {
  await openShip(page);
  await write(report(page), leader.sorting);

  await runTests(page);

  await expect(summary(page)).toHaveText('All 2 tests pass. 1 of 2 checks pass.', loaded);
  const fast = shipCheck(page, 'Fast on 60,000 votes');
  await expect(fast).toContainText('✓');
  await expect(fast).toContainText(/\d\.\d\d s on 60,000 votes/);
  await expect(fast).not.toContainText('The limit is a second.');
  const leaves = shipCheck(page, 'Leaves the votes as they were');
  await expect(leaves).toContainText('✗');
  await expect(leaves).toContainText(
    "It changed the list it was given, so the poll's votes would change with every call.",
  );

  await write(report(page), leader.fixed);
  await runTests(page);
  await expect(summary(page)).toHaveText('All 2 tests pass. All 2 checks pass.', loaded);
  await expect(page.getByText('Stage 4 done.')).toBeVisible();
  await expect(page.getByRole('button', { name: /Leader/ })).toContainText('Done');
});

test("a Ship stage's Printed tab shows only what the code prints as it loads", async ({ page }) => {
  await openShip(page);
  await write(
    report(page),
    `print("loading")\n\n\n${leader.fixed.replace('    return', '    print("counting")\n    return')}`,
  );

  await runTests(page);
  await expect(summary(page)).toHaveText('All 2 tests pass. All 2 checks pass.', loaded);
  await page.getByRole('tab', { name: 'Printed' }).click();

  const printed = page.getByRole('tabpanel', { name: 'Printed' });
  await expect(printed).toContainText('loading');
  await expect(printed).not.toContainText('counting');
});
