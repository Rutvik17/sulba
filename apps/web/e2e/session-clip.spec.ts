import { expect, type Page, test } from '@playwright/test';

// The clip runs on requestAnimationFrame. With Playwright's clock paused before the page loads,
// the clip moves only when a test runs the clock, so every step lands on a known moment.
async function open(page: Page) {
  await page.clock.install({ time: 0 });
  await page.clock.pauseAt(1000);
  await page.goto('/');
}

const clip = (page: Page) => page.locator('[data-session]');
const checks = (page: Page) => clip(page).locator('.checks');
// Notes fade in and out, so a note counts as shown once it is fully opaque.
const note = (page: Page, which: 'hidden' | 'done') => clip(page).locator(`.${which}-note`);

test("the assistant's tests pass, one check fails, and the fix passes both", async ({ page }) => {
  await open(page);

  await page.clock.runFor(2900);
  await expect(clip(page).locator('.results li[data-state="pass"]')).toHaveCount(2);
  await expect(checks(page)).toHaveText('1 of 2 pass');
  await expect(note(page, 'hidden')).toHaveCSS('opacity', '1');

  await page.clock.runFor(7000);
  await expect(checks(page)).toHaveText('2 of 2 pass');
  await expect(note(page, 'done')).toHaveCSS('opacity', '1');
  await expect(note(page, 'hidden')).toHaveCSS('opacity', '0');
});

test('the clip plays once, rests on its last frame, and replays on request', async ({ page }) => {
  await open(page);

  await page.clock.runFor(14_000);
  await expect(checks(page)).toHaveText('2 of 2 pass');
  const replay = clip(page).getByRole('button', { name: 'Replay' });
  await expect(replay).toBeVisible();

  await page.clock.runFor(5000);
  await expect(checks(page)).toHaveText('2 of 2 pass');

  await replay.click();
  await page.clock.runFor(500);
  await expect(checks(page)).toHaveText('Not run yet');
  await expect(clip(page).getByRole('button', { name: 'Pause' })).toBeVisible();
});

test('the clip never changes height while it plays', async ({ page }) => {
  await open(page);

  const heights = new Set<number>();
  for (const step of [0, 2700, 1400, 1100, 1300, 1500, 1200, 1500, 1700]) {
    await page.clock.runFor(step);
    const box = await clip(page).boundingBox();
    heights.add(Math.round(box?.height ?? 0));
  }

  expect([...heights]).toHaveLength(1);
});

test('Pause stops the clip and Play starts it again', async ({ page }) => {
  await open(page);
  await page.clock.runFor(1000);

  await clip(page).getByRole('button', { name: 'Pause' }).click();
  await page.clock.runFor(4000);
  await expect(checks(page)).toHaveText('Not run yet');

  await clip(page).getByRole('button', { name: 'Play' }).click();
  await page.clock.runFor(2000);
  await expect(checks(page)).toHaveText('1 of 2 pass');
});

test.describe('with reduced motion', () => {
  test.use({ contextOptions: { reducedMotion: 'reduce' } });

  test('the clip shows the finished review, still, with nothing to pause', async ({ page }) => {
    await page.goto('/');

    await expect(checks(page)).toHaveText('2 of 2 pass');
    await expect(note(page, 'done')).toHaveCSS('opacity', '1');
    await expect(clip(page).getByRole('button', { name: 'Pause' })).toBeHidden();
  });
});
