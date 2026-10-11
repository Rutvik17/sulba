import { expect, test } from '@playwright/test';

test('a button in a React island takes presses from a pointer and from the keyboard', async ({
  page,
  hasTouch,
}) => {
  await page.goto('/gallery/');
  // Astro drops the island's ssr attribute once React has taken it over.
  await expect(page.locator('astro-island')).not.toHaveAttribute('ssr');
  const button = page.getByRole('button', { name: 'Press' });
  const count = page.getByRole('status');
  await expect(count).toHaveText('Pressed 0 times');

  await (hasTouch ? button.tap() : button.click());
  await expect(count).toHaveText('Pressed once');

  await button.focus();
  await page.keyboard.press('Enter');
  await page.keyboard.press('Space');
  await expect(count).toHaveText('Pressed 3 times');
});
