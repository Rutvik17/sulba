import { expect, type Page, test } from '@playwright/test';

/** Opens the gallery once React has taken over every island; Astro then drops each ssr attribute. */
async function openGallery(page: Page) {
  await page.goto('/gallery/');
  await expect(page.locator('astro-island[ssr]')).toHaveCount(0);
}

test('a button in a React island takes presses from a pointer and from the keyboard', async ({
  page,
  hasTouch,
}) => {
  await openGallery(page);
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

test('a segmented choice picks the option pressed, and arrow keys pick the next one', async ({
  page,
}) => {
  await openGallery(page);
  const where = page.getByRole('radiogroup', { name: 'Where tests run' });
  await expect(where.getByRole('radio', { name: 'Browser' })).toBeChecked();

  await where.getByText('Your machine').click();
  await expect(where.getByRole('radio', { name: 'Your machine' })).toBeChecked();
  await page.keyboard.press('ArrowLeft');
  await expect(where.getByRole('radio', { name: 'Browser' })).toBeChecked();
});

test('arrow keys pass over an option that is unavailable', async ({ page }) => {
  await openGallery(page);
  const layout = page.getByRole('radiogroup', { name: 'Layout' });
  await expect(layout.getByRole('radio', { name: 'Output' })).toBeDisabled();

  await layout.getByText('Split').click();
  await page.keyboard.press('ArrowRight');

  await expect(layout.getByRole('radio', { name: 'Editor' })).toBeChecked();
});

test('tabs show the panel of the tab chosen, by pointer or by arrow keys', async ({ page }) => {
  await openGallery(page);
  const panel = page.getByRole('tabpanel');
  await expect(page.getByRole('tab', { name: 'Brief' })).toHaveAttribute('aria-selected', 'true');
  await expect(panel).toHaveText('Write sigmoid(z) and make its tests pass.');

  await page.getByRole('tab', { name: 'Explanation' }).click();
  await expect(panel).toHaveText('Sigmoid maps any number to one between 0 and 1.');

  await page.keyboard.press('ArrowLeft');
  await expect(page.getByRole('tab', { name: 'Hints' })).toHaveAttribute('aria-selected', 'true');
  await expect(panel).toHaveText('Start from the formula: 1 / (1 + e^-z).');
});

test('a tab that is not open yet can be neither chosen nor reached by arrow keys', async ({
  page,
}) => {
  await openGallery(page);
  const solution = page.getByRole('tab', { name: 'Solution' });
  await expect(solution).toHaveAttribute('aria-disabled', 'true');

  await page.getByRole('tab', { name: 'Tests' }).click();
  await page.keyboard.press('End');
  await expect(page.getByRole('tab', { name: 'Tests' })).toHaveAttribute('aria-selected', 'true');

  await solution.click({ force: true });
  await expect(solution).toHaveAttribute('aria-selected', 'false');
});
