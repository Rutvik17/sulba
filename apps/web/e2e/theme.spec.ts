import { expect, type Page, test } from '@playwright/test';

const dark = 'rgb(14, 14, 14)';
const light = 'rgb(250, 250, 248)';

const background = (page: Page) => expect(page.locator('body'));

for (const [scheme, colour] of [
  ['dark', dark],
  ['light', light],
] as const) {
  test(`a page follows a ${scheme} device setting`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/');

    await background(page).toHaveCSS('background-color', colour);
  });
}

test('a theme a learner picks applies at once and is kept after a reload', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');

  await page.getByRole('button', { name: 'Theme' }).click();
  await page.getByRole('radio', { name: 'Dark' }).check();
  await background(page).toHaveCSS('background-color', dark);

  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await background(page).toHaveCSS('background-color', dark);
});

test('picking System follows the device setting again and forgets the choice', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');

  await page.getByRole('button', { name: 'Theme' }).click();
  await page.getByRole('radio', { name: 'Dark' }).check();
  await page.getByRole('radio', { name: 'System' }).check();

  await expect(page.locator('html')).not.toHaveAttribute('data-theme');
  await background(page).toHaveCSS('background-color', light);
  expect(await page.evaluate(() => localStorage.getItem('sulba:theme'))).toBeNull();
});

test('the theme control works from the keyboard', async ({ page }) => {
  await page.goto('/');
  const toggle = page.getByRole('button', { name: 'Theme' });
  const panel = page.getByRole('group', { name: 'Theme' });

  await toggle.focus();
  await page.keyboard.press('Enter');
  await expect(panel).toBeVisible();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('radio', { name: 'System' })).toBeFocused();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('radio', { name: 'Light' })).toBeChecked();
  await page.keyboard.press('Escape');

  await expect(panel).toBeHidden();
  await expect(toggle).toBeFocused();
});

// The fixture course's lab (playwright.config.ts), whose workspace has an editor.
const lab = '/demo/counting/tallies/';
const dracula = 'rgb(40, 42, 54)';

/** Opens the lab and its theme panel, once the workspace's editor is on the page. */
async function openPanel(page: Page) {
  await page.goto(lab);
  await expect(page.getByRole('textbox', { name: 'tally.py', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Theme', exact: true }).click();
}

const editor = (page: Page) => page.locator('.cm-editor');

test('an editor theme a learner picks colours the editor at once and is kept after a reload', async ({
  page,
}) => {
  await openPanel(page);

  await page.getByRole('radio', { name: 'Dracula' }).check();
  await expect(editor(page)).toHaveCSS('background-color', dracula);

  await page.reload();
  await expect(editor(page)).toHaveCSS('background-color', dracula);
  await page.getByRole('button', { name: 'Theme', exact: true }).click();
  await expect(page.getByRole('radio', { name: 'Dracula' })).toBeChecked();
});

test("picking Sulba's editor theme follows the page's theme again and forgets the choice", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: 'dark' });
  await openPanel(page);
  const sulba = await editor(page).evaluate((element) => getComputedStyle(element).backgroundColor);

  await page.getByRole('radio', { name: 'Dracula' }).check();
  await page.getByRole('radio', { name: 'Sulba' }).check();

  await expect(editor(page)).toHaveCSS('background-color', sulba);
  expect(await page.evaluate(() => localStorage.getItem('sulba:editor-theme'))).toBeNull();
});

test('the editor themes are chosen from the keyboard, by the arrow keys', async ({ page }) => {
  await openPanel(page);
  const themes = page.getByRole('group', { name: 'Editor theme', exact: true });

  await themes.getByRole('radio', { name: 'Sulba' }).focus();
  await page.keyboard.press('ArrowDown');

  await expect(themes.getByRole('radio', { name: 'GitHub Light' })).toBeChecked();
  await expect(editor(page)).toHaveCSS('background-color', 'rgb(255, 255, 255)');
});

test('a page without an editor offers no editor themes', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Theme', exact: true }).click();

  await expect(page.getByRole('radio', { name: 'System' })).toBeVisible();
  await expect(page.getByRole('group', { name: 'Editor theme', exact: true })).toHaveCount(0);
});
