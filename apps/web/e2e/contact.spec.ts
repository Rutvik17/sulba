import { expect, type Page, test } from '@playwright/test';

// Turnstile, stood in for: it hands over the test token at once, as Cloudflare's test keys do.
const turnstile = `window.turnstile = {
  render(container, options) { setTimeout(() => options.callback('XXXX.DUMMY.TOKEN.XXXX')); return 'widget'; },
  reset() {},
};`;

// Every test that sends stands in for /api/contact too, so no test ever emails the studio.
async function open(page: Page, answer: { status: number; body: object }) {
  const sent: unknown[] = [];
  await page.route('https://challenges.cloudflare.com/**', (route) =>
    route.fulfill({ contentType: 'text/javascript', body: turnstile }),
  );
  await page.route('**/api/contact', async (route) => {
    sent.push(route.request().postDataJSON());
    await route.fulfill({
      status: answer.status,
      contentType: 'application/json',
      body: JSON.stringify(answer.body),
    });
  });
  await page.goto('/contact/');
  return sent;
}

async function write(page: Page) {
  await page.getByLabel('Name').fill('Ada Lovelace');
  await page.getByLabel('Email').fill('ada@example.com');
  await page.getByLabel('Message').fill('Hello');
  await page.getByRole('button', { name: 'Send' }).click();
}

test('the contact page loads nothing from other sites until the form is used', async ({ page }) => {
  const origins = new Set<string>();
  page.on('request', (request) => origins.add(new URL(request.url()).origin));

  await page.goto('/contact/', { waitUntil: 'networkidle' });

  expect([...origins]).toEqual([new URL(page.url()).origin]);
});

test('a message goes with its Turnstile token, and the page says where the reply will go', async ({
  page,
}) => {
  const sent = await open(page, { status: 200, body: { sent: true } });

  await write(page);

  await expect(page.getByRole('status')).toHaveText("Sent. We'll reply to ada@example.com.");
  expect(sent).toEqual([
    {
      name: 'Ada Lovelace',
      email: 'ada@example.com',
      message: 'Hello',
      token: 'XXXX.DUMMY.TOKEN.XXXX',
    },
  ]);
  await expect(page.getByLabel('Message')).toHaveValue('');
});

test('a message the server turns down keeps what was written and says why', async ({ page }) => {
  await open(page, { status: 503, body: { problem: 'unavailable' } });

  await write(page);

  await expect(page.getByRole('status')).toHaveText(
    "Messages can't be sent right now. Try again later.",
  );
  await expect(page.getByLabel('Message')).toHaveValue('Hello');
});

test('an empty form says under each field what it needs, and sends nothing', async ({ page }) => {
  const sent = await open(page, { status: 200, body: { sent: true } });

  await page.getByRole('button', { name: 'Send' }).click();

  await expect(page.getByLabel('Name')).toBeFocused();
  await expect(page.getByLabel('Name')).toHaveAttribute('aria-invalid', 'true');
  await expect(page.getByLabel('Name')).toHaveAccessibleDescription('Enter your name');
  await expect(page.getByLabel('Email')).toHaveAccessibleDescription('Enter your email address');
  await expect(page.getByLabel('Message')).toHaveAccessibleDescription('Enter a message');
  await expect(page.getByText('Enter your name')).toBeVisible();
  expect(sent).toEqual([]);
});

test('spaces alone count as empty, and an email address has to look like one', async ({ page }) => {
  const sent = await open(page, { status: 200, body: { sent: true } });

  await page.getByLabel('Name').fill('   ');
  await page.getByLabel('Email').fill('ada@');
  await page.getByLabel('Message').fill('Hello');
  await page.getByRole('button', { name: 'Send' }).click();

  await expect(page.getByLabel('Name')).toBeFocused();
  await expect(page.getByLabel('Name')).toHaveAccessibleDescription('Enter your name');
  await expect(page.getByLabel('Email')).toHaveAccessibleDescription(
    'Enter an email address in the correct format, like name@example.com',
  );
  await expect(page.getByLabel('Message')).not.toHaveAttribute('aria-invalid');
  expect(sent).toEqual([]);
});

test('a message clears as soon as its field is right, and the form then sends', async ({
  page,
}) => {
  const sent = await open(page, { status: 200, body: { sent: true } });
  await page.getByRole('button', { name: 'Send' }).click();

  await page.getByLabel('Name').fill('Ada Lovelace');

  await expect(page.getByLabel('Name')).not.toHaveAttribute('aria-invalid');
  await expect(page.getByText('Enter your name')).toBeHidden();
  await expect(page.getByLabel('Email')).toHaveAttribute('aria-invalid', 'true');

  await write(page);

  await expect(page.getByRole('status')).toHaveText("Sent. We'll reply to ada@example.com.");
  expect(sent).toHaveLength(1);
});

test('the landing and the footer lead to the contact page', async ({ page }) => {
  await page.goto('/');
  await page
    .getByRole('region', { name: 'For companies' })
    .getByRole('link', { name: 'Write to us' })
    .click();
  await expect(page).toHaveURL('/contact/');

  await expect(
    page.getByRole('contentinfo').getByRole('link', { name: 'Contact' }),
  ).toHaveAttribute('aria-current', 'page');
});

// These reach the real endpoint, which turns them down before it calls Turnstile or Resend.
test('the contact endpoint takes only well-formed messages, sent with POST', async ({
  request,
}) => {
  expect((await request.get('/api/contact')).status()).toBe(405);
  expect((await request.post('/api/contact', { data: { name: 'Ada' } })).status()).toBe(400);
});
