import { expect, test } from '@playwright/test';

test('the home page loads', async ({ page }) => {
  const response = await page.goto('/academy/');

  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle('Sulba · The school of the AI era');
  await expect(
    page.getByRole('heading', { level: 1, name: 'The school of the AI era' }),
  ).toBeVisible();
});

test('the home page lists how a lab runs and the first course', async ({ page }) => {
  await page.goto('/academy/');

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

test('the Privacy Policy names who handles your information, and the Terms the law that governs them', async ({
  page,
}) => {
  const privacy = await page.goto('/privacy/');

  expect(privacy?.status()).toBe(200);
  await expect(page).toHaveTitle('Privacy Policy · Sulba');
  await expect(page.getByRole('heading', { level: 1, name: 'Privacy Policy' })).toBeVisible();
  await expect(page.getByRole('table').getByRole('link')).toHaveText([
    'Supabase, Inc.',
    'GitHub, Inc.',
    'Google LLC',
    'Cloudflare, Inc.',
    'Resend (Plus Five Five, Inc.)',
    'Apple Inc.',
  ]);
  // Words either side of a link, a label or code keep their space.
  await expect(page.getByRole('main')).toContainText(
    'The bot check. Before your message is sent, Cloudflare Turnstile checks',
  );
  await expect(page.getByRole('main')).toContainText(
    'in your browser (as sulba:reviews), so it can work out',
  );
  await expect(page.getByRole('main')).toContainText(
    'runs in a frame from challenges.cloudflare.com. It sends',
  );

  const terms = await page.goto('/terms/');

  expect(terms?.status()).toBe(200);
  await expect(page).toHaveTitle('Terms of Use · Sulba');
  await expect(page.getByRole('heading', { level: 1, name: 'Terms of Use' })).toBeVisible();
  await expect(page.getByRole('main')).toContainText(
    'please write to us through the contact page and give us 30 days',
  );
  await expect(
    page.getByText('These Terms are governed by the laws of the Province of Ontario'),
  ).toBeVisible();
});

test('the footer and the contact page lead to the Privacy Policy', async ({ page }) => {
  await page.goto('/contact/');
  await page.getByRole('main').getByRole('link', { name: 'Privacy Policy' }).click();
  await expect(page).toHaveURL('/privacy/');

  const footer = page.getByRole('contentinfo');
  await expect(footer.getByRole('link', { name: 'Privacy' })).toHaveAttribute(
    'aria-current',
    'page',
  );
  await footer.getByRole('link', { name: 'Terms' }).click();
  await expect(page).toHaveURL('/terms/');
});

test('the footer leads to the about page and marks it as the page you are on', async ({ page }) => {
  await page.goto('/academy/');
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
  await expect(page).toHaveURL('/academy/');
});

test('a keyboard user can skip past the top bar to the content', async ({ page, browserName }) => {
  test.skip(
    browserName === 'webkit',
    "WebKit's Tab key skips links, as Safari's does until the user turns on Press Tab to highlight each item",
  );
  await page.goto('/academy/');

  await page.keyboard.press('Tab');
  const skip = page.getByRole('link', { name: 'Skip to content' });
  await expect(skip).toBeFocused();
  await expect(skip).toBeInViewport();
  await page.keyboard.press('Enter');

  await expect(page).toHaveURL(/#main$/);
});

test('pages never link to the repository', async ({ page }) => {
  await page.goto('/academy/');

  await expect(page.locator('a[href*="github.com/Rutvik17/sulba"]')).toHaveCount(0);
});

test('the home page loads nothing from other sites', async ({ page }) => {
  const origins = new Set<string>();
  page.on('request', (request) => origins.add(new URL(request.url()).origin));

  await page.goto('/academy/', { waitUntil: 'networkidle' });

  expect([...origins]).toEqual([new URL(page.url()).origin]);
});

test('pages ask search engines not to index them before launch', async ({ request }) => {
  const response = await request.get('/academy/');

  expect(response.headers()['x-robots-tag']).toBe('noindex');
});

test('no other site can show a page in a frame, the app’s pages included', async ({ request }) => {
  for (const path of ['/academy/', '/app/oauth/consent?authorization_id=x']) {
    const response = await request.get(path, {
      headers: { 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Dest': 'document' },
    });
    expect(response.headers()['x-frame-options'], path).toBe('DENY');
    expect(response.headers()['content-security-policy'], path).toBe("frame-ancestors 'none'");
  }
});

test('each page links the icons a browser and a phone show for it, and the site serves them', async ({
  page,
  request,
}) => {
  await page.goto('/academy/');

  await expect(page.locator('link[rel="icon"]')).toHaveCount(2);
  await expect(page.locator('link[rel="apple-touch-icon"]')).toHaveCount(1);
  for (const [path, type] of [
    ['/favicon.ico', 'image/'],
    ['/icon.svg', 'image/svg+xml'],
    ['/apple-touch-icon.png', 'image/png'],
  ] as const) {
    const response = await request.get(path);
    expect(response.status(), path).toBe(200);
    expect(response.headers()['content-type'], path).toContain(type);
  }
});
