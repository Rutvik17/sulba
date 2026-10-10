import { expect, test } from '@playwright/test';

test('the home page loads', async ({ page }) => {
  const response = await page.goto('/');

  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle('Sulba · The school of the AI era');
  await expect(
    page.getByRole('heading', { level: 1, name: 'The school of the AI era' }),
  ).toBeVisible();
});

test('the home page lists how a module runs and the first course', async ({ page }) => {
  await page.goto('/');

  await expect(
    page.getByRole('region', { name: 'How each module runs' }).getByRole('heading', { level: 3 }),
  ).toHaveText([/Sketch/, /Build it yourself/, /Design/, /Build with AI/, /Review/]);
  await expect(page.getByRole('region', { name: 'Courses' }).getByRole('listitem')).toHaveText([
    /Beginner/,
    /Intermediate/,
    /Advanced/,
    /Master/,
    /Elite/,
  ]);
});

test('an unknown address shows the not-found page with a 404 status', async ({ page }) => {
  const response = await page.goto('/no-such-page/');

  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1, name: 'Page not found' })).toBeVisible();
  await page.getByRole('link', { name: 'Go to the home page' }).click();
  await expect(page).toHaveURL('/');
});

test('a keyboard user can skip past the top bar to the content', async ({ page }) => {
  await page.goto('/');

  await page.keyboard.press('Tab');
  const skip = page.getByRole('link', { name: 'Skip to content' });
  await expect(skip).toBeFocused();
  await expect(skip).toBeInViewport();
  await page.keyboard.press('Enter');

  await expect(page).toHaveURL(/#main$/);
});

test('every page links to the source code, as the AGPL asks', async ({ page }) => {
  await page.goto('/');

  await expect(
    page.getByRole('contentinfo').getByRole('link', { name: 'Source code' }),
  ).toHaveAttribute('href', 'https://github.com/Rutvik17/sulba');
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
