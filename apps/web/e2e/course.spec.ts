import { expect, type Page, test } from '@playwright/test';
import { signedIn, standIn, supabase } from './supabase';

// The tests build the site from the content package's fixture course (playwright.config.ts): the
// course Demo, whose level First has the module Counting, with the lab Tallies and its 4 stages,
// and the module Interviews, with the lab Pairs and its one Problem stage.
const path = '/demo/';
const stages = ['stg_demo01', 'stg_demo02', 'stg_demo03', 'stg_demo04'];

async function passed(page: Page, ...ids: string[]) {
  await page.addInitScript((each) => {
    for (const id of each) localStorage.setItem(`sulba:passed:${id}`, '1');
  }, ids);
}

const tallies = (page: Page) => page.getByRole('listitem').filter({ hasText: 'Tallies' });
// What the lab builds, its stages and its time, as on its own page.
const facts = ['tally.py, then report.py', '2 Build, 1 Catch, 1 Ship', 'About 40 minutes'];

test("a course's page lists its levels, modules and labs, with what each lab builds and its time", async ({
  page,
}) => {
  const origins = new Set<string>();
  page.on('request', (request) => origins.add(new URL(request.url()).origin));
  const response = await page.goto(path, { waitUntil: 'networkidle' });

  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle('Demo · Sulba');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Demo');
  const level = page.getByRole('region', { name: 'First' });
  await expect(level.getByRole('heading', { level: 3 })).toHaveText(['Counting', 'Interviews']);
  await expect(level.getByRole('link', { name: 'Tallies' })).toHaveAttribute(
    'href',
    '/demo/counting/tallies/',
  );
  await expect(tallies(page)).toContainText(
    "Count the votes in a small poll, then work out each choice's share.",
  );
  // With no stage passed, there is no progress to show, and nothing is asked of Supabase.
  await expect(tallies(page).getByRole('definition')).toHaveText(facts);
  await expect(tallies(page).getByText('Progress')).toBeHidden();
  const pairs = page.getByRole('listitem').filter({ hasText: 'Pairs' });
  await expect(pairs.getByRole('definition')).toHaveText([
    'pairs.py',
    '1 Problem',
    'About 20 minutes',
  ]);
  expect(origins.has(supabase)).toBe(false);
});

test('each lab says how many of its stages are done in this browser', async ({ page }) => {
  await passed(page, 'stg_demo01');
  await page.goto(path);
  await expect(tallies(page).getByRole('definition')).toHaveText([...facts, '1 of 4 stages done']);
});

test('a lab with every stage passed is done', async ({ page }) => {
  await passed(page, ...stages);
  await page.goto(path);
  await expect(tallies(page).getByRole('definition')).toHaveText([...facts, 'Done']);
});

test('signed in, the stages passed on other devices count too', async ({ page }) => {
  await standIn(page, { passed: [{ stage_id: 'stg_demo02', caught: null, problems: null }] });
  await signedIn(page);
  await passed(page, 'stg_demo01');
  await page.goto(path);
  await expect(tallies(page).getByRole('definition')).toHaveText([...facts, '2 of 4 stages done']);
});

test('the home page links the course, and a lab page links back to its module', async ({
  page,
}) => {
  await page.goto('/');
  const card = page.getByRole('region', { name: 'Courses' }).getByRole('link', { name: 'Demo' });
  await expect(card).toHaveAttribute('href', path);
  await card.click();
  await expect(page).toHaveURL(path);

  await page.getByRole('link', { name: 'Tallies' }).click();
  await expect(page).toHaveURL('/demo/counting/tallies/');
  await page.getByRole('link', { name: 'First · Counting' }).click();
  await expect(page).toHaveURL('/demo/#counting');
  await expect(page.getByRole('heading', { level: 3, name: 'Counting' })).toBeInViewport();
});
