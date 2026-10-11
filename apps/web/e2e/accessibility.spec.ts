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

  test(`the contact form's messages have no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    // Turnstile starts loading when the form is first used; no test reaches Cloudflare.
    await page.route('https://challenges.cloudflare.com/**', (route) => route.abort());
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/contact/');
    await page.getByRole('button', { name: 'Send' }).click();
    await expect(page.getByLabel('Name')).toHaveAttribute('aria-invalid', 'true');

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

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
