import { expect, type Page, test } from '@playwright/test';

// The clip runs on requestAnimationFrame. With Playwright's clock paused before the page loads,
// the clip moves only when a test runs the clock, so every step lands on a known moment.
async function open(page: Page) {
  await page.clock.install({ time: 0 });
  await page.clock.pauseAt(1000);
  await page.goto('/');
}

const clip = (page: Page) => page.locator('[data-session]');
const summary = (page: Page) => clip(page).locator('.summary');
// Notes fade in and out, so a note counts as shown once it is fully opaque.
const note = (page: Page, which: 'fail' | 'done') => clip(page).locator(`.${which}-note`);

test('the clip fails two tests, then passes all four', async ({ page }) => {
  await open(page);

  await page.clock.runFor(2700);
  await expect(summary(page)).toHaveText('2 failed · 2 passed');
  await expect(note(page, 'fail')).toHaveCSS('opacity', '1');
  await expect(note(page, 'fail')).toContainText(
    'Returned every order in the table, expected none',
  );

  await page.clock.runFor(7200);
  await expect(summary(page)).toHaveText('4 passed');
  await expect(note(page, 'done')).toHaveCSS('opacity', '1');
  await expect(note(page, 'fail')).toHaveCSS('opacity', '0');
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
  await expect(summary(page)).toHaveText('Not run yet');

  await clip(page).getByRole('button', { name: 'Play' }).click();
  await page.clock.runFor(2000);
  await expect(summary(page)).toHaveText('2 failed · 2 passed');
});

test.describe('with reduced motion', () => {
  test.use({ contextOptions: { reducedMotion: 'reduce' } });

  test('the clip shows the finished session, still, with nothing to pause', async ({ page }) => {
    await page.goto('/');

    await expect(summary(page)).toHaveText('4 passed');
    await expect(note(page, 'done')).toHaveCSS('opacity', '1');
    await expect(clip(page).getByRole('button', { name: 'Pause' })).toBeHidden();
  });
});
