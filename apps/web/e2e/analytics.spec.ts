import AxeBuilder from '@axe-core/playwright';
import { expect, type Page, test } from '@playwright/test';

// A first visit: nothing is stored, so the site asks before it counts anything.
test.use({ storageState: { cookies: [], origins: [] } });

// Cloudflare's script, stood in for, so no test is ever counted. Returns each time it loads.
async function watch(page: Page) {
  const loads: string[] = [];
  await page.route('https://static.cloudflareinsights.com/**', (route) => {
    loads.push(route.request().url());
    return route.fulfill({ contentType: 'text/javascript', body: '' });
  });
  return loads;
}

const question = (page: Page) => page.getByRole('region', { name: 'Can we count your visit?' });

test("nothing is counted until a visitor allows it, and Don't allow is remembered", async ({
  page,
}) => {
  const loads = await watch(page);
  await page.goto('/');

  await expect(question(page)).toBeVisible();
  await question(page).getByRole('button', { name: "Don't allow" }).click();
  await expect(question(page)).toBeHidden();

  await page.goto('/about/');
  await expect(question(page)).toBeHidden();
  expect(loads).toEqual([]);
});

test("Allow loads Cloudflare's script with the site's token, on this page and the next", async ({
  page,
}) => {
  const loads = await watch(page);
  await page.goto('/');

  await question(page).getByRole('button', { name: 'Allow', exact: true }).click();

  await expect(question(page)).toBeHidden();
  await expect.poll(() => loads.length).toBe(1);
  await expect(page.locator('script[data-cf-beacon]')).toHaveAttribute(
    'data-cf-beacon',
    '{"token":"e2e-analytics-token"}',
  );

  await page.goto('/about/');
  await expect(question(page)).toBeHidden();
  await expect.poll(() => loads.length).toBe(2);
});

test('Privacy choices in the footer asks again, and the new answer holds from the next page', async ({
  page,
}) => {
  const loads = await watch(page);
  await page.goto('/');
  await question(page).getByRole('button', { name: 'Allow', exact: true }).click();
  await expect.poll(() => loads.length).toBe(1);

  await page.getByRole('contentinfo').getByRole('button', { name: 'Privacy choices' }).click();
  await expect(question(page)).toBeVisible();
  await expect(question(page).getByRole('button', { name: 'Allow', exact: true })).toBeFocused();
  await question(page).getByRole('button', { name: "Don't allow" }).click();

  await page.goto('/about/');
  await expect(question(page)).toBeHidden();
  expect(loads).toHaveLength(1);
});

for (const scheme of ['dark', 'light'] as const) {
  test(`the question has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({ page }) => {
    await watch(page);
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/');
    await expect(question(page)).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });
}
