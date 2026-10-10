import { expect, type Page, test } from '@playwright/test';

// "How every lab runs" has two layouts. On a wide screen one frame is pinned and its stages play
// with the scroll; on a phone the stages stand one under another, finished. Each test runs on the
// layout it describes.
const lab = (page: Page) => page.locator('[data-lab]');
const active = (page: Page) => lab(page).locator('.layer[data-active]');
const stage = (page: Page, name: string) =>
  page
    .getByRole('region', { name: 'How every lab runs' })
    .getByRole('button', { name: new RegExp(name) });

async function open(page: Page) {
  await page.goto('/');
  // The track's length follows the pinned block, which is measured once the page is laid out.
  await expect(lab(page)).toHaveAttribute('style', /--pin-height/);
}

// Scrolls the frame a share of the way through its track: 0 as it pins, 1 as it lets go.
async function scrollTo(page: Page, progress: number) {
  await page.evaluate((progress) => {
    const track = document.querySelector('[data-lab] .track');
    const pin = document.querySelector('[data-lab] .pin');
    if (!(track instanceof HTMLElement && pin instanceof HTMLElement)) throw new Error('No track');
    const box = track.getBoundingClientRect();
    const top = Number.parseFloat(getComputedStyle(pin).top) || 0;
    window.scrollTo(0, window.scrollY + box.top - top + progress * (box.height - pin.offsetHeight));
  }, progress);
}

test.describe('on a wide screen', () => {
  test.skip(({ isMobile }) => isMobile, 'A phone shows the stages one under another');

  test('each stage plays as the reader scrolls, forwards and backwards', async ({ page }) => {
    await open(page);
    await expect(lab(page)).toHaveAttribute('data-mode', 'scroll');

    await scrollTo(page, 0.01);
    await expect(stage(page, 'Build')).toHaveAttribute('aria-current', 'step');
    await expect(active(page).locator('.summary')).toHaveText('Not run yet');

    await scrollTo(page, 0.31);
    await expect(active(page).locator('.summary')).toHaveText('4 of 4 pass');

    await scrollTo(page, 0.43);
    await expect(stage(page, 'Catch')).toHaveAttribute('aria-current', 'step');
    await expect(active(page).locator('.checks')).toHaveText('0 of 5 pass');

    await scrollTo(page, 0.65);
    await expect(active(page).locator('.checks')).toHaveText('1 of 5 pass');

    await scrollTo(page, 0.76);
    await expect(stage(page, 'Ship')).toHaveAttribute('aria-current', 'step');
    await expect(active(page).locator('.results li').first()).toHaveAttribute('data-state', 'fail');
    await expect(active(page).locator('.ready')).toBeHidden();

    await scrollTo(page, 1);
    await expect(active(page).locator('.ready')).toBeVisible();

    await scrollTo(page, 0.31);
    await expect(stage(page, 'Build')).toHaveAttribute('aria-current', 'step');
    await expect(active(page).locator('.summary')).toHaveText('4 of 4 pass');
  });

  test('the frame stays put and keeps one height while its stages play', async ({ page }) => {
    await open(page);

    const boxes = new Set<string>();
    for (const progress of [0, 0.15, 0.31, 0.47, 0.65, 0.8, 1]) {
      await scrollTo(page, progress);
      const box = await lab(page).locator('.view').boundingBox();
      boxes.add(`${Math.round(box?.y ?? 0)} ${Math.round(box?.height ?? 0)}`);
    }

    expect([...boxes]).toHaveLength(1);
  });

  test('a stage name scrolls the frame to that stage', async ({ page }) => {
    await open(page);
    await scrollTo(page, 0.01);

    await stage(page, 'Ship').click();

    await expect(stage(page, 'Ship')).toHaveAttribute('aria-current', 'step');
    await expect(stage(page, 'Build')).not.toHaveAttribute('aria-current');
  });

  test.describe('with reduced motion', () => {
    test.use({ contextOptions: { reducedMotion: 'reduce' } });

    test('the names switch the frame between finished stages', async ({ page }) => {
      await open(page);
      await expect(lab(page)).toHaveAttribute('data-mode', 'still');
      await expect(stage(page, 'Build')).toHaveAttribute('aria-pressed', 'true');
      await expect(active(page).locator('.summary')).toHaveText('4 of 4 pass');

      await stage(page, 'Catch').click();

      await expect(stage(page, 'Catch')).toHaveAttribute('aria-pressed', 'true');
      await expect(stage(page, 'Build')).toHaveAttribute('aria-pressed', 'false');
      await expect(active(page).locator('.checks')).toHaveText('1 of 5 pass');
    });
  });
});

test.describe('on a phone', () => {
  test.skip(
    ({ isMobile }) => !isMobile,
    'A wide screen shows one frame that plays with the scroll',
  );

  test('the three stages stand one under another, each finished', async ({ page }) => {
    await page.goto('/');

    const stills = lab(page).locator('.stills > li');
    await expect(stills).toHaveCount(3);
    await expect(stills.nth(0).locator('.summary')).toHaveText('4 of 4 pass');
    await expect(stills.nth(1).locator('.checks')).toHaveText('1 of 5 pass');
    await expect(stills.nth(2).locator('.ready')).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      ),
    ).toBe(0);
  });
});
