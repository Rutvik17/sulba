import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const wcag = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

for (const path of ['/', '/no-such-page/']) {
  test(`${path} has no WCAG 2.2 AA violations`, async ({ page }) => {
    await page.goto(path);

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });
}
