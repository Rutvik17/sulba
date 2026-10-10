import { expect, test } from '@playwright/test';

test('the home page loads', async ({ page }) => {
  const response = await page.goto('/');

  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle('Sulba');
  await expect(page.getByRole('heading', { level: 1, name: 'Sulba' })).toBeVisible();
});

test('an unknown address shows the not-found page with a 404 status', async ({ page }) => {
  const response = await page.goto('/no-such-page/');

  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1, name: 'Page not found' })).toBeVisible();
  await page.getByRole('link', { name: 'Go to the home page' }).click();
  await expect(page).toHaveURL('/');
});

test('the home page loads nothing from other sites', async ({ page }) => {
  const origins = new Set<string>();
  page.on('request', (request) => origins.add(new URL(request.url()).origin));

  await page.goto('/', { waitUntil: 'networkidle' });

  expect([...origins]).toEqual([new URL(page.url()).origin]);
});

test('pages ask search engines not to index them before launch', async ({ request }) => {
  const response = await request.get('/');

  expect(response.headers()['x-robots-tag']).toBe('noindex');
});
