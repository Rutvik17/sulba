import { expect, type Page, test } from '@playwright/test';

/** Keyboard focus on one button and the pointer over another, so a screenshot shows both states. */
async function focusAndHover(page: Page, focus: string, hover: string) {
  await page.getByRole('button', { name: focus }).first().focus();
  await page.keyboard.press('Shift+Tab');
  await page.keyboard.press('Tab');
  await page.getByRole('button', { name: hover }).first().hover();
}

for (const scheme of ['dark', 'light'] as const) {
  test(`buttons in the ${scheme} theme`, async ({ page, isMobile }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/gallery/');
    if (!isMobile) await focusAndHover(page, 'Show a hint', 'Run tests');

    await expect(page.getByRole('region', { name: 'Button' })).toHaveScreenshot(
      `button-${scheme}.png`,
    );
  });
}
