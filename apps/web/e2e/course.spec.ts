import { expect, type Page, test } from '@playwright/test';
import { signedIn, standIn, supabase } from './supabase';

// The tests build the site from the content package's fixture course (playwright.config.ts): the
// course Demo, whose level First has the module Counting, with the lab Tallies and its 4 stages,
// and the optional module Interviews, with the lab Pairs and its one Problem stage and the lab Poll
// design and its one Design stage, and whose level Second has the module Ledgers, with the lab
// Ledger and its 6 stages, which runs on the learner's machine.
const path = '/academy/demo/';
const stages = ['stg_demo01', 'stg_demo02', 'stg_demo03', 'stg_demo04'];
const ledger = ['stg_demo06', 'stg_demo07', 'stg_demo08', 'stg_demo09', 'stg_demo11', 'stg_demo12'];

async function passed(page: Page, ...ids: string[]) {
  await page.addInitScript((each) => {
    for (const id of each) localStorage.setItem(`sulba:passed:${id}`, '1');
  }, ids);
}

const level = (page: Page) => page.getByRole('region', { name: 'First' });
const counting = (page: Page) => level(page).getByRole('button', { name: /Counting/ });
/** A lab's row in its open module: the list item around its heading. */
const row = (page: Page, title: string) =>
  level(page).getByRole('heading', { level: 4, name: title }).locator('xpath=ancestor::li[1]');
const tallies = (page: Page) => row(page, 'Tallies');
const next = (page: Page) => page.getByText('Next lab').locator('xpath=../..');
// What the lab builds, its stages and its time, as on its own page.
const facts = ['tally.py, then report.py', '2 Build, 1 Catch, 1 Ship', 'About 40 minutes'];

test("a course's page lists its levels, with their facts, and their modules, closed, with their labs' titles", async ({
  page,
}) => {
  const origins = new Set<string>();
  page.on('request', (request) => origins.add(new URL(request.url()).origin));
  const response = await page.goto(path, { waitUntil: 'networkidle' });

  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle('Demo · Sulba');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Demo');
  await expect(level(page).locator('dl').first().getByRole('definition')).toHaveText([
    '2, 1 of them optional',
    '3',
    'About 40 minutes, and about 50 minutes more in the optional module',
    'Any laptop: every lab runs in your browser',
  ]);
  await expect(level(page).getByRole('heading', { level: 3 })).toHaveText([
    /1\s*Counting/,
    /2\s*Interviews/,
  ]);
  await expect(counting(page)).toHaveAttribute('aria-expanded', 'false');
  await expect(level(page).getByText('1 lab · About 40 minutes')).toBeVisible();
  await expect(level(page).getByText('Optional · 2 labs · About 50 minutes')).toBeVisible();
  // Every lab's title shows, and links its page, with every module closed.
  await expect(
    level(page)
      .getByRole('list', { name: 'Labs in Counting' })
      .getByRole('link', { name: 'Tallies' }),
  ).toHaveAttribute('href', '/academy/demo/counting/tallies/');
  await expect(
    page.getByText("Count the votes in a small poll, then work out each choice's share."),
  ).toBeHidden();
  // With no stage passed, there is no progress to show, and nothing is asked of Supabase.
  await expect(level(page).getByText('Progress')).toBeHidden();
  expect(origins.has(supabase)).toBe(false);
});

test('a module opens to its labs, with what each builds, its stages and its time, and closes again', async ({
  page,
}) => {
  await page.goto(path);
  await counting(page).click();

  await expect(counting(page)).toHaveAttribute('aria-expanded', 'true');
  await expect(tallies(page)).toContainText(
    "Count the votes in a small poll, then work out each choice's share.",
  );
  await expect(tallies(page).getByRole('definition')).toHaveText(facts);
  await expect(tallies(page).getByRole('link', { name: 'Tallies' })).toHaveAttribute(
    'href',
    '/academy/demo/counting/tallies/',
  );
  await expect(level(page).getByRole('list', { name: 'Labs in Counting' })).toBeHidden();

  await counting(page).click();
  await expect(counting(page)).toHaveAttribute('aria-expanded', 'false');
  await expect(tallies(page)).toBeHidden();
});

test('Show all modules opens every module, and Hide all modules closes them', async ({ page }) => {
  await page.goto(path);
  await level(page).getByRole('button', { name: 'Show all modules' }).click();

  const modules = level(page).getByRole('heading', { level: 3 }).getByRole('button');
  await expect(modules).toHaveCount(2);
  for (const module of await modules.all())
    await expect(module).toHaveAttribute('aria-expanded', 'true');
  await expect(row(page, 'Pairs').getByRole('definition')).toHaveText([
    'pairs.py',
    '1 Problem',
    'About 20 minutes',
  ]);
  // A lab of designs builds no file, so it names none.
  await expect(row(page, 'Poll design').getByRole('definition')).toHaveText([
    '1 Design',
    'About 30 minutes',
  ]);

  await page.getByRole('button', { name: 'Hide all modules' }).click();
  for (const module of await modules.all())
    await expect(module).toHaveAttribute('aria-expanded', 'false');
});

test("a new learner's next lab is the course's first", async ({ page }) => {
  await page.goto(path);
  await expect(next(page).getByRole('link', { name: 'Tallies' })).toHaveAttribute(
    'href',
    '/academy/demo/counting/tallies/',
  );
  await expect(next(page)).toContainText('Module 1 · Counting · About 40 minutes');
  await expect(next(page)).toContainText('Start');
});

test('a lab partway through is the next lab, with how many of its stages are done', async ({
  page,
}) => {
  await passed(page, 'stg_demo01');
  await page.goto(path);

  await expect(next(page).getByRole('link', { name: 'Tallies' })).toBeVisible();
  await expect(next(page)).toContainText('Module 1 · Counting · 1 of 4 stages done');
  await expect(next(page)).toContainText('Continue');
  await expect(level(page).getByText('0 of 1 labs done')).toBeVisible();
  await expect(level(page).locator('dl').first()).toContainText('0 of 3 labs done');
  await counting(page).click();
  await expect(tallies(page)).toContainText('1 of 4 stages done');
});

test("after a lab that's done, the next lab is the one after it, past an optional module", async ({
  page,
}) => {
  await passed(page, ...stages);
  await page.goto(path);

  await expect(next(page).getByRole('link', { name: 'Ledger' })).toHaveAttribute(
    'href',
    '/academy/demo/ledgers/ledger/',
  );
  await expect(next(page)).toContainText('Module 1 · Ledgers · About 1 hour');
  // The module's row, under its title.
  await expect(level(page).getByText('1 lab · About 40 minutes').locator('..')).toContainText(
    'Done',
  );
  await counting(page).click();
  await expect(tallies(page)).toContainText('Done');
});

test("an optional module's lab is next once one of its labs is started", async ({ page }) => {
  await passed(page, ...stages, 'stg_demo05');
  await page.goto(path);

  await expect(next(page).getByRole('link', { name: 'Poll design' })).toHaveAttribute(
    'href',
    '/academy/demo/interviews/poll-design/',
  );
  await expect(next(page)).toContainText('Module 2 · Interviews · About 30 minutes');
});

test("with every other lab done, an optional module's first lab is next", async ({ page }) => {
  await passed(page, ...stages, ...ledger);
  await page.goto(path);

  await expect(next(page).getByRole('link', { name: 'Pairs' })).toHaveAttribute(
    'href',
    '/academy/demo/interviews/pairs/',
  );
  await expect(next(page)).toContainText('Module 2 · Interviews · About 20 minutes');
});

test('with every lab done, there is no next lab', async ({ page }) => {
  await passed(page, ...stages, 'stg_demo05', 'stg_demo10', ...ledger);
  await page.goto(path);

  await expect(level(page).locator('dl').first()).toContainText('3 of 3 labs done');
  await expect(page.getByText('Next lab')).toBeHidden();
});

test('signed in, the stages passed on other devices count too', async ({ page }) => {
  await standIn(page, { passed: [{ stage_id: 'stg_demo02', caught: null, problems: null }] });
  await signedIn(page);
  await passed(page, 'stg_demo01');
  await page.goto(path);

  await expect(next(page)).toContainText('2 of 4 stages done');
  await counting(page).click();
  await expect(tallies(page)).toContainText('2 of 4 stages done');
});

test('the home page links the course, and a lab page links back to its module, open', async ({
  page,
}) => {
  await page.goto('/academy/');
  const card = page.getByRole('region', { name: 'Courses' }).getByRole('link', { name: 'Demo' });
  await expect(card).toHaveAttribute('href', path);
  await card.click();
  await expect(page).toHaveURL(path);

  await page
    .getByRole('list', { name: 'Labs in Counting' })
    .getByRole('link', { name: 'Tallies' })
    .click();
  await expect(page).toHaveURL('/academy/demo/counting/tallies/');
  await page.getByRole('link', { name: 'First · Counting' }).click();
  await expect(page).toHaveURL('/academy/demo/#counting');
  await expect(counting(page)).toHaveAttribute('aria-expanded', 'true');
  await expect(page.getByRole('heading', { level: 3, name: /Counting/ })).toBeInViewport();
});

test.describe('without JavaScript', () => {
  test.use({ javaScriptEnabled: false });

  test('every module shows open, under a plain heading', async ({ page }) => {
    await page.goto(path);

    await expect(level(page).getByRole('heading', { level: 3 }).getByRole('button')).toHaveCount(0);
    await expect(tallies(page).getByRole('definition')).toHaveText(facts);
    await expect(page.getByRole('button', { name: 'Show all modules' })).toBeHidden();
  });
});
