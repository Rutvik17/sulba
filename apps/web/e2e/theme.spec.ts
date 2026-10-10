import { expect, test } from '@playwright/test';

for (const [scheme, background] of [
  ['dark', 'rgb(14, 14, 14)'],
  ['light', 'rgb(250, 250, 248)'],
] as const) {
  test(`a page follows a ${scheme} device setting`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/');

    await expect(page.locator('body')).toHaveCSS('background-color', background);
  });
}
