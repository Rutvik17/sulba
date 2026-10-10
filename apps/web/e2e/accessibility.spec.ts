import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const wcag = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

for (const scheme of ['dark', 'light'] as const) {
  for (const path of ['/', '/about/', '/contact/', '/no-such-page/']) {
    test(`${path} has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(path);

      const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

      expect(results.violations).toEqual([]);
    });
  }

  test(`the open theme panel has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/');
    await page.getByRole('button', { name: 'Theme' }).click();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });
}
