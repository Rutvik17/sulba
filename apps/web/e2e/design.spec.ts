import { expect, type Page, test } from '@playwright/test';

// The tests build the site from the content package's fixture course (playwright.config.ts), whose
// module Interviews has the lab Poll design: one Design stage, with 30 minutes, two follow-up
// questions and a rubric of three points, two of which pass it.
const path = '/demo/interviews/poll-design/';
const key = 'sulba:design:stg_demo10';
const points = [
  'Counts each vote once',
  'Says who reads the results, and when',
  'Keeps a record that a recount can check',
] as const;

/** Keeps a first attempt whose answers came in 25 minutes after it started, no point marked met. */
async function answered(page: Page) {
  await page.addInitScript((each) => {
    // The script runs on every load, so a reload finds what the page has kept since.
    if (localStorage.getItem(each) !== null) return;
    const state = {
      started: Date.now() - 26 * 60_000,
      attempts: 1,
      design: 'One table of ballots, each with its id.',
      handedIn: true,
      answers: ['Count the box again from its ballots.', 'The table grows first.'],
      answered: 25 * 60,
      marks: [false, false, false],
      marked: false,
    };
    localStorage.setItem(each, JSON.stringify(state));
  }, key);
}

const timer = (page: Page) => page.getByRole('timer');
const design = (page: Page) => page.getByRole('textbox', { name: 'Your design' });
const mark = (page: Page, point: string, choice: 'Met' | 'Not met') =>
  page.getByRole('radiogroup', { name: point }).getByText(choice, { exact: true }).click();

test('a design shows its brief once it starts, its questions once handed in, then its rubric', async ({
  page,
}) => {
  await page.goto(path);
  const start = page.getByRole('button', { name: 'Start' });
  await expect(start).toBeVisible();
  await expect(page.getByText('The town clerk wants a service')).toBeHidden();
  await expect(timer(page)).toBeHidden();

  await start.click();

  await expect(page.locator(':focus')).toContainText('The town clerk wants a service');
  await expect(page.getByText('when the polls close at 8 pm')).toBeVisible();
  await expect(timer(page)).toHaveText(/^0:0\d of 30:00$/);
  const handIn = page.getByRole('button', { name: 'Hand in the design' });
  await expect(handIn).toBeDisabled();
  await design(page).fill('One table of ballots, each with its id, and a count of the ids.');
  await handIn.click();

  const first = page.getByRole('textbox', { name: 'Two counts of the same box disagree.' });
  await expect(first).toBeFocused();
  await expect(design(page)).not.toBeEditable();
  await page.getByRole('tab', { name: 'Explanation' }).click();
  await expect(page.getByRole('tabpanel', { name: 'Explanation' })).toHaveText(
    'Opens when you hand in your answers.',
  );
  const answers = page.getByRole('button', { name: 'Hand in the answers' });
  await first.fill('Count the box again from its ballots.');
  await expect(answers).toBeDisabled();
  await page
    .getByRole('textbox', { name: 'The town doubles its voters.' })
    .fill('The table of ballots grows first.');
  await answers.click();

  await expect(page.getByRole('heading', { name: 'Rubric' })).toBeFocused();
  await expect(page.getByText(/^Handed in at 0:\d\d, inside its 30 minutes\.$/)).toBeVisible();
  await expect(page.getByText('The clerk reads them at 8 pm, when the polls close.')).toBeVisible();
  await expect(page.getByRole('tabpanel', { name: 'Explanation' })).toContainText(
    'A design that counts each ballot once',
  );
  const stopped = (await timer(page).textContent()) ?? '';
  expect(stopped).toMatch(/^0:\d\d of 30:00$/);

  // The attempt is kept: a reload opens the rubric again, with the clock where it stopped.
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Rubric' })).toBeVisible();
  await expect(design(page)).toHaveValue(
    'One table of ballots, each with its id, and a count of the ids.',
  );
  await expect(timer(page)).toHaveText(stopped);
});

test('a design that meets enough of its rubric passes the stage', async ({ page }) => {
  await answered(page);
  await page.goto(path);
  await expect(timer(page)).toHaveText('25:00 of 30:00');
  // Each point starts as not met.
  await expect(
    page
      .getByRole('radiogroup', { name: points[2] })
      .getByRole('radio', { name: 'Not met', exact: true }),
  ).toBeChecked();

  await mark(page, points[0], 'Met');
  await mark(page, points[1], 'Met');
  await page.getByRole('button', { name: 'Finish marking' }).click();

  await expect(page.locator(':focus')).toHaveText(
    'Stage 1 done. You met 2 of 3 points, and it needs 2.',
  );
  await expect(page.getByRole('button', { name: /A poll service/ })).toContainText('Done');
  // The marks are settled: each point shows the mark it was given.
  await expect(page.getByRole('radiogroup')).toHaveCount(0);
  await expect(page.getByText('Not met', { exact: true })).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Start again' })).toBeHidden();

  await page.reload();
  await expect(page.getByText('Stage 1 done. You met 2 of 3 points')).toBeVisible();
});

test('a design that misses its rubric starts again from the same design', async ({ page }) => {
  await answered(page);
  await page.goto(path);

  await mark(page, points[0], 'Met');
  await mark(page, points[1], 'Met');
  await mark(page, points[1], 'Not met');
  await page.getByRole('button', { name: 'Finish marking' }).click();

  await expect(page.locator(':focus')).toHaveText('You met 1 of 3 points, and the stage needs 2.');
  await expect(page.getByRole('button', { name: /A poll service/ })).not.toContainText('Done');
  await page.getByRole('button', { name: 'Start again' }).click();

  await expect(design(page)).toBeFocused();
  await expect(design(page)).toHaveValue('One table of ballots, each with its id.');
  await expect(page.getByText('Attempt 2')).toBeVisible();
  await expect(timer(page)).toHaveText(/^0:0\d of 30:00$/);
  await expect(page.getByRole('heading', { name: 'Rubric' })).toBeHidden();
  // The model design stays open once it has been read.
  await page.getByRole('tab', { name: 'Explanation' }).click();
  await expect(page.getByRole('tabpanel', { name: 'Explanation' })).toContainText(
    'A design that counts each ballot once',
  );
});

test('a design passed on another device opens in full, with no clock', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('sulba:passed:stg_demo10', '1'));
  await page.goto(path);

  await expect(page.getByText('Stage 1 done.')).toBeVisible();
  await expect(page.getByText(points[0])).toBeVisible();
  await expect(page.getByRole('radiogroup')).toHaveCount(0);
  await expect(timer(page)).toBeHidden();
  await page.getByRole('tab', { name: 'Explanation' }).click();
  await expect(page.getByRole('tabpanel', { name: 'Explanation' })).toContainText(
    'A design that counts each ballot once',
  );
});

test('a lab of designs loads no Python', async ({ page }) => {
  const asked: string[] = [];
  page.on('request', (request) => asked.push(new URL(request.url()).pathname));
  await page.goto(path, { waitUntil: 'networkidle' });

  await expect(page.getByRole('button', { name: 'Start' })).toBeVisible();
  expect(asked.filter((each) => each.startsWith('/pyodide/'))).toEqual([]);
});
