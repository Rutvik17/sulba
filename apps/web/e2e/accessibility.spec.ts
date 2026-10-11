import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const wcag = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

for (const scheme of ['dark', 'light'] as const) {
  for (const path of [
    '/',
    '/about/',
    '/contact/',
    '/privacy/',
    '/terms/',
    '/no-such-page/',
    '/gallery/',
  ]) {
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

  for (const [what, trigger, role] of [
    ['side panel', 'Open the review', 'dialog'],
    ['menu', 'Session', 'menu'],
  ] as const) {
    test(`the gallery's open ${what} has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
      page,
    }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto('/gallery/');
      await expect(page.locator('astro-island[ssr]')).toHaveCount(0);
      await page.getByRole('button', { name: trigger }).click();
      await expect(page.getByRole(role)).toBeVisible();
      // React Aria marks an overlay data-entering until it has finished sliding or fading in.
      await expect(page.locator('[data-entering]')).toHaveCount(0);

      const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

      expect(results.violations).toEqual([]);
    });
  }
}
