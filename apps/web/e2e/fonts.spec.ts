import { expect, test } from '@playwright/test';

test('text is set in Geist, served by the site itself', async ({ page }) => {
  const fonts: string[] = [];
  page.on('response', (response) => {
    if (response.request().resourceType() === 'font') fonts.push(response.url());
  });

  await page.goto('/');
  const loaded = await page.evaluate(async () => {
    await document.fonts.ready;
    return [...document.fonts]
      .filter((font) => font.status === 'loaded')
      .map((font) => font.family);
  });

  expect(loaded.some((family) => family.includes('Geist Variable'))).toBe(true);
  expect(fonts.length).toBeGreaterThan(0);
  for (const url of fonts) expect(new URL(url).origin).toBe(new URL(page.url()).origin);
});
