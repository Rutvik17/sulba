import { expect, test } from '@playwright/test';
import { learner, signedIn, standIn, supabase } from './supabase';

// The app, apps/app, which the site's Worker serves under /app/ (decision record 47).

test('signed out, the app offers sign-in that comes back to it, and loads nothing from Supabase', async ({
  page,
}) => {
  const origins = new Set<string>();
  page.on('request', (request) => origins.add(new URL(request.url()).origin));

  await page.goto('/app/', { waitUntil: 'networkidle' });

  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Sign in to Sulba');
  await expect(page.getByRole('link', { name: 'Sign in' })).toHaveAttribute(
    'href',
    '/sign-in/?next=%2Fapp%2F',
  );
  expect(origins.has(supabase)).toBe(false);
});

test('signed in on the site, the app knows who is signed in, and signs them out', async ({
  page,
}) => {
  const calls = await standIn(page);
  await signedIn(page);

  await page.goto('/app/');
  await expect(page.getByText(`Signed in as ${learner.email}.`)).toBeVisible();

  await page.getByRole('button', { name: 'Sign out' }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Sign in to Sulba');
  expect(calls.logouts).toBe(1);
  expect(await page.evaluate(() => localStorage.getItem('sulba:session'))).toBeNull();
});

test('an address under /app/ is answered with the app, which says when it has no such page', async ({
  page,
}) => {
  const response = await page.goto('/app/nothing/here/');

  expect(response?.status()).toBe(200);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Page not found');
  await page.getByRole('link', { name: 'Go to Sulba' }).click();
  await expect(page).toHaveURL(/\/app\/$/);
});
