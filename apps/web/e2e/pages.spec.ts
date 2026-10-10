import { expect, test } from '@playwright/test';

test('the home page loads', async ({ page }) => {
  const response = await page.goto('/');

  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle('Sulba · The school of the AI era');
  await expect(
    page.getByRole('heading', { level: 1, name: 'The school of the AI era' }),
  ).toBeVisible();
});

test('the home page lists how a lab runs and the first course', async ({ page }) => {
  await page.goto('/');

  await expect(
    page.getByRole('region', { name: 'How every lab runs' }).getByRole('heading', { level: 3 }),
  ).toHaveText([/Build/, /Catch/, /Ship/]);
  await expect(page.getByRole('region', { name: 'Courses' }).getByRole('listitem')).toHaveText([
    /Beginner/,
    /Intermediate/,
    /Advanced/,
    /Master/,
    /Elite/,
  ]);
});

test('the about page says what Sulba is, where its name comes from, what it values and who makes it', async ({
  page,
}) => {
  const response = await page.goto('/about/');

  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle('About · Sulba');
  await expect(page.getByRole('heading', { level: 1, name: 'About Sulba' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'The name' })).toContainText(
    'A cord of 12 equal lengths, pegged into sides of 3, 4 and 5, makes a right angle, because 3² + 4² = 5².',
  );
  await expect(
    page.getByRole('region', { name: 'What we value' }).getByRole('heading', { level: 3 }),
  ).toHaveText([
    'Fundamentals first',
    'Real problems',
    'Review every line',
    'Correct before complete',
  ]);
  await expect(page.getByRole('region', { name: 'Team' }).getByRole('listitem')).toHaveText([
    /Rutvik Patel\s*Founder/,
  ]);
});

test('the footer leads to the about page and marks it as the page you are on', async ({ page }) => {
  await page.goto('/');
  const about = page.getByRole('contentinfo').getByRole('link', { name: 'About' });

  await expect(about).not.toHaveAttribute('aria-current');
  await about.click();

  await expect(page).toHaveURL('/about/');
  await expect(about).toHaveAttribute('aria-current', 'page');
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

test('pages never link to the repository', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('a[href*="github.com/Rutvik17/sulba"]')).toHaveCount(0);
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
