import { expect, type Page, test } from '@playwright/test';

const dark = 'rgb(14, 14, 14)';
const light = 'rgb(250, 250, 248)';

const background = (page: Page) => expect(page.locator('body'));

for (const [scheme, colour] of [
  ['dark', dark],
  ['light', light],
] as const) {
  test(`a page follows a ${scheme} device setting`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/');

    await background(page).toHaveCSS('background-color', colour);
  });
}

test('a theme a learner picks applies at once and is kept after a reload', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');

  await page.getByRole('button', { name: 'Theme' }).click();
  await page.getByRole('radio', { name: 'Dark' }).check();
  await background(page).toHaveCSS('background-color', dark);

  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await background(page).toHaveCSS('background-color', dark);
});

test('picking System follows the device setting again and forgets the choice', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');

  await page.getByRole('button', { name: 'Theme' }).click();
  await page.getByRole('radio', { name: 'Dark' }).check();
  await page.getByRole('radio', { name: 'System' }).check();

  await expect(page.locator('html')).not.toHaveAttribute('data-theme');
  await background(page).toHaveCSS('background-color', light);
  expect(await page.evaluate(() => localStorage.getItem('sulba:theme'))).toBeNull();
});

test('the theme control works from the keyboard', async ({ page }) => {
  await page.goto('/');
  const toggle = page.getByRole('button', { name: 'Theme' });
  const panel = page.getByRole('group', { name: 'Theme' });

  await toggle.focus();
  await page.keyboard.press('Enter');
  await expect(panel).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('radio', { name: 'System' })).toBeFocused();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('radio', { name: 'Light' })).toBeChecked();
  await page.keyboard.press('Escape');

  await expect(panel).toBeHidden();
  await expect(toggle).toBeFocused();
});
