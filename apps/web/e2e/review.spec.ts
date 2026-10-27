import { expect, type Page, test } from '@playwright/test';
import { signedIn, standIn, supabase } from './supabase';

// The fixture course's first stage, Count, has two cards; its second, Share, has one.
const firstCard = "How many of the poll's 3 votes are yes?";
const secondCard = 'What does count add up?';
const start = new Date('2026-10-15T09:00:00Z');

test.use({ timezoneId: 'UTC' });

async function passed(page: Page, ...stages: string[]) {
  await page.addInitScript((ids) => {
    for (const id of ids) localStorage.setItem(`sulba:passed:${id}`, '1');
  }, stages);
}

const counts = (page: Page) => page.locator('[data-counts]');
const front = (page: Page) => page.locator('[data-front]');

async function rate(page: Page, rating: string) {
  await page.getByRole('button', { name: 'Show answer' }).click();
  await page.getByRole('button', { name: new RegExp(`^${rating} `) }).click();
}

test('with no stage passed, there are no cards, and nothing is asked of Supabase', async ({
  page,
}) => {
  const origins = new Set<string>();
  page.on('request', (request) => origins.add(new URL(request.url()).origin));
  await page.goto('/academy/review/', { waitUntil: 'networkidle' });

  await expect(
    page.getByText('No cards yet. Each stage you pass adds its cards here.'),
  ).toBeVisible();
  await expect(page.getByText('Loading your cards…')).toBeHidden();
  expect(origins.has(supabase)).toBe(false);
});

test("a passed stage's cards come up new, and each comes back as its rating says", async ({
  page,
}) => {
  await page.clock.setFixedTime(start);
  await passed(page, 'stg_demo01');
  await page.goto('/academy/review/');

  await expect(counts(page)).toHaveText('0 to review · 2 new');
  await expect(front(page)).toHaveText(firstCard);
  await expect(page.getByRole('link', { name: 'Tallies · Count' })).toHaveAttribute(
    'href',
    '/academy/demo/counting/tallies/?stage=count',
  );
  await expect(page.getByText('New', { exact: true })).toBeVisible();

  await page.getByRole('button', { name: 'Show answer' }).click();
  await expect(page.locator('[data-back]')).toHaveText('2.');
  await expect(page.locator('[data-back]')).toBeFocused();
  for (const [name, interval] of [
    ['Forgot', '1 minute'],
    ['Hard', '6 minutes'],
    ['Good', '10 minutes'],
    ['Easy', '8 days'],
  ]) {
    await expect(page.getByRole('button', { name: `${name} Back in ${interval}` })).toBeVisible();
  }
  await page.getByRole('button', { name: /^Good / }).click();

  await expect(front(page)).toHaveText(secondCard);
  await expect(front(page)).toBeFocused();
  await expect(counts(page)).toHaveText('0 to review · 1 new');
  await rate(page, 'Easy');

  // Nothing else is due, so the first card's 10-minute step comes early.
  await expect(front(page)).toHaveText(firstCard);
  await expect(counts(page)).toHaveText('1 to review · 0 new');
  await page.getByText('History').click();
  await expect(page.locator('[data-history-list] li')).toHaveText([
    'Thursday 15 October 2026, 09:00: Good',
  ]);

  await page.clock.setFixedTime(new Date(start.getTime() + 10 * 60_000));
  await rate(page, 'Good');
  await expect(
    page.getByText('Nothing is due. The next card is due on Saturday 17 October 2026.'),
  ).toBeFocused();

  // The reviews stay in this browser, and so does the schedule they make.
  await page.reload();
  await expect(
    page.getByText('Nothing is due. The next card is due on Saturday 17 October 2026.'),
  ).toBeVisible();
  const kept = await page.evaluate(() => JSON.parse(localStorage.getItem('sulba:reviews') ?? '[]'));
  expect(kept.map((review: { rating: number }) => review.rating)).toEqual([3, 4, 3]);
});

test('signed in, cards come from the stages and reviews in the account, and new reviews go to it', async ({
  page,
}) => {
  await page.clock.setFixedTime(start);
  const reviewed = {
    id: '10000000-0000-4000-8000-000000000001',
    card_id: 'crd_demo03',
    rating: 4,
    reviewed_at: '2026-10-01T09:00:00.000Z',
  };
  const calls = await standIn(page, {
    passed: [{ stage_id: 'stg_demo02', caught: null, problems: null }],
    reviews: [reviewed],
  });
  await signedIn(page);
  await page.goto('/academy/review/');

  await expect(front(page)).toHaveText("What is a choice's share of the votes?");
  await expect(counts(page)).toHaveText('1 to review · 0 new');
  await page.getByText('History').click();
  await expect(page.locator('[data-history-list] li')).toHaveText([
    'Thursday 1 October 2026, 09:00: Easy',
  ]);

  await rate(page, 'Good');
  await expect.poll(() => calls.reviews.length, { timeout: 10_000 }).toBe(1);
  expect(calls.reviews[0]).toMatchObject({ card_id: 'crd_demo03', rating: 3 });
});
