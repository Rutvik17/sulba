import { expect, test } from '@playwright/test';

// The learning site's pages moved under /academy/ (public/_redirects). The course's old addresses
// are the real course's, which the fixture course leaves in place.

test("the site's address opens the Academy, with a temporary redirect", async ({ request }) => {
  const response = await request.get('/', { maxRedirects: 0 });

  expect(response.status()).toBe(302);
  expect(response.headers().location).toBe('/academy/');
});

test('the old addresses lead to the same pages under /academy/ for good, with their query', async ({
  request,
}) => {
  for (const [from, to] of [
    ['/review/', '/academy/review/'],
    ['/review', '/academy/review/'],
    ['/ai-engineering/', '/academy/ai-engineering/'],
    ['/ai-engineering', '/academy/ai-engineering/'],
    [
      '/ai-engineering/pytorch/tensors-and-autograd/?stage=tensors',
      '/academy/ai-engineering/pytorch/tensors-and-autograd/?stage=tensors',
    ],
  ] as const) {
    const response = await request.get(from, { maxRedirects: 0 });
    expect(response.status(), from).toBe(301);
    expect(response.headers().location, from).toBe(to);
  }
});

test('a link to an old address keeps its fragment', async ({ page }) => {
  await page.goto('/review/#card');

  await expect(page).toHaveURL('/academy/review/#card');
});
