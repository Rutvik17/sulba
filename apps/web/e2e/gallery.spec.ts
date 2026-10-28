import { expect, type Page, test } from '@playwright/test';
import { islandsHydrated } from './islands';

/** Opens the gallery once React has taken over every island. */
async function openGallery(page: Page) {
  await page.goto('/gallery/');
  await islandsHydrated(page);
}

test('a button in a React island takes presses from a pointer and from the keyboard', async ({
  page,
  hasTouch,
}) => {
  await openGallery(page);
  const button = page.getByRole('button', { name: 'Press' });
  const count = page.getByRole('region', { name: 'Button' }).getByRole('status');
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

test('a slider moves by a step with the arrow keys and to its ends with Home and End', async ({
  page,
}) => {
  await openGallery(page);
  const rate = page.getByRole('slider', { name: 'Learning rate' });
  const shown = page.getByRole('group', { name: 'Learning rate' }).locator('output');
  await expect(shown).toHaveText('0.10');

  await rate.focus();
  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('ArrowRight');
  await expect(shown).toHaveText('0.12');
  await expect(rate).toHaveValue('0.12');

  await page.keyboard.press('End');
  await expect(shown).toHaveText('1.00');
  await page.keyboard.press('Home');
  await expect(shown).toHaveText('0.00');
});

test('a slider through a list of stops shows and announces each stop', async ({ page }) => {
  await openGallery(page);
  const decay = page.getByRole('slider', { name: 'Weight decay' });
  const shown = page.getByRole('group', { name: 'Weight decay' }).locator('output');
  await expect(shown).toHaveText('0.01');
  await expect(decay).toHaveAttribute('aria-valuetext', '0.01');

  await decay.focus();
  await page.keyboard.press('ArrowRight');
  await expect(shown).toHaveText('0.1');
  await expect(decay).toHaveAttribute('aria-valuetext', '0.1');
  await page.keyboard.press('Home');
  await expect(decay).toHaveAttribute('aria-valuetext', '0.0001');
});

/** Presses the right end of a slider's track, the 24 px row at the bottom of the slider. */
async function pressTrackEnd(page: Page, name: string) {
  const slider = page.getByRole('group', { name });
  await slider.scrollIntoViewIfNeeded();
  const box = await slider.boundingBox();
  if (!box) throw new Error(`The ${name} slider has no box`);
  await page.mouse.click(box.x + box.width - 1, box.y + box.height - 12);
}

test('a slider takes its value from where the track is pressed', async ({ page }) => {
  await openGallery(page);

  await pressTrackEnd(page, 'Epochs');

  await expect(page.getByRole('slider', { name: 'Epochs' })).toHaveValue('100');
});

test('a slider that is disabled cannot be moved', async ({ page }) => {
  await openGallery(page);
  const batch = page.getByRole('slider', { name: 'Batch size' });
  await expect(batch).toBeDisabled();

  await pressTrackEnd(page, 'Batch size');

  await expect(batch).toHaveValue('32');
});

test('a side panel takes the focus, closes with Escape, and gives the focus back', async ({
  page,
}) => {
  await openGallery(page);
  const open = page.getByRole('button', { name: 'Open the review' });
  const panel = page.getByRole('dialog', { name: 'Review' });

  await open.click();
  await expect(panel).toBeVisible();
  // React Aria focuses the dialog itself, or the first thing in it that takes focus.
  const focusInPanel = () =>
    page.evaluate(() => document.activeElement?.closest('[role="dialog"]') != null);
  await expect.poll(focusInPanel).toBe(true);
  await page.keyboard.press('Escape');

  await expect(panel).toBeHidden();
  await expect(open).toBeFocused();
});

test('a side panel closes from its Close button and from a button that ends it', async ({
  page,
}) => {
  await openGallery(page);
  const open = page.getByRole('button', { name: 'Open the review' });
  const panel = page.getByRole('dialog', { name: 'Review' });

  await open.click();
  await panel.getByRole('button', { name: 'Close' }).click();
  await expect(panel).toBeHidden();

  await open.click();
  await panel.getByRole('button', { name: 'Next session' }).click();
  await expect(panel).toBeHidden();
});

test('a side panel closes when the page beside it is pressed', async ({ page, isMobile }) => {
  test.skip(isMobile, 'On a phone the panel fills the screen');
  await openGallery(page);
  const panel = page.getByRole('dialog', { name: 'Review' });

  await page.getByRole('button', { name: 'Open the review' }).click();
  await expect(panel).toBeVisible();
  await page.mouse.click(10, 400);

  await expect(panel).toBeHidden();
});

test('a menu opens from its button, moves with the arrow keys and acts on Enter', async ({
  page,
}) => {
  await openGallery(page);
  const chosen = page.getByRole('region', { name: 'Menu' }).getByRole('status');
  const menu = page.getByRole('menu');

  await page.getByRole('button', { name: 'Session' }).click();
  await expect(menu).toBeVisible();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');

  await expect(menu).toBeHidden();
  await expect(chosen).toHaveText('Chose: Copy the starter code');
});

test('a menu closes with Escape, gives the focus back, and skips an item that is disabled', async ({
  page,
}) => {
  await openGallery(page);
  const trigger = page.getByRole('button', { name: 'Session' });

  await trigger.click();
  const disabled = page.getByRole('menuitem', { name: 'Download the solution' });
  await expect(disabled).toHaveAttribute('aria-disabled', 'true');
  await page.keyboard.press('ArrowUp');
  await expect(page.getByRole('menuitem', { name: 'Report a mistake' })).toBeFocused();
  await page.keyboard.press('Escape');

  await expect(page.getByRole('menu')).toBeHidden();
  await expect(trigger).toBeFocused();
});

/** The editable editor in the gallery, and its code area. */
function editor(page: Page) {
  const section = page.getByRole('region', { name: 'Code editor' });
  return { section, code: section.getByRole('textbox', { name: 'model.py' }) };
}

/** Puts the cursor at the end of the editor's code, or with `start`, at its start. */
async function focusCode(page: Page, where: 'start' | 'end' = 'end') {
  const { code } = editor(page);
  const lines = code.locator('.cm-line');
  // A click on the line, then Home or End: the same keys on every platform. Moving to the start
  // or end of the whole file takes Command on the iPhone project and Control elsewhere. The click
  // lands at the line's start: on a phone the longest line is wider than the editor, so a click in
  // a line's middle would scroll the editor sideways, past the start of what's typed next.
  await (where === 'start' ? lines.first() : lines.last()).click({ position: { x: 4, y: 4 } });
  await expect(code).toBeFocused();
  await page.keyboard.press(where === 'start' ? 'Home' : 'End');
}

// The phone projects stand in for touch screens, which have no keyboard shortcuts. The iPhone one
// would also need Command, which Playwright presses only on a Mac.
const shortcuts = 'Keyboard shortcuts need a keyboard';

test('the editor marks a name Python cannot find, and counts it', async ({ page }) => {
  await openGallery(page);
  const { section } = editor(page);

  await expect(section.locator('.cm-lintRange-error')).toHaveText('bias');
  await expect(section.getByText('1 error, 0 warnings')).toBeVisible();
});

test('the editor offers the names in the file as one is typed', async ({ page }) => {
  await openGallery(page);
  const { code } = editor(page);

  await focusCode(page);
  await page.keyboard.type('\n\nsig');
  const sigmoid = page.getByRole('option').filter({ hasText: 'sigmoid' });
  // The editor makes the list out of sight and moves it beside the cursor a frame later. A click
  // that came first would scroll the page away from the editor, and the list would stay hidden.
  await expect(sigmoid).toBeInViewport();
  // The editor ignores Enter for a moment after the list opens, so a press can't pick by accident.
  await sigmoid.click();

  await expect(code.locator('.cm-line').last()).toHaveText('sigmoid');
});

test('the list of names shows whole where it reaches past the editor', async ({ page }) => {
  await openGallery(page);
  const { section } = editor(page);

  await focusCode(page);
  await page.keyboard.type('\n\nsig');
  const list = page.getByRole('listbox', { name: 'Completions' });

  // The list reaches below the code, where the editor's frame would cut it off if it sat inside.
  await expect(list).toBeInViewport({ ratio: 1 });
  const listBox = await list.boundingBox();
  const codeBox = await section
    .locator('.cm-editor', { has: page.getByRole('textbox', { name: 'model.py' }) })
    .boundingBox();
  if (!listBox || !codeBox) throw new Error('The list or the code has no box');
  expect(listBox.y + listBox.height).toBeGreaterThan(codeBox.y + codeBox.height);
});

test('Ctrl+/ comments a line out and back in', async ({ page, isMobile }) => {
  test.skip(isMobile, shortcuts);
  await openGallery(page);
  const first = editor(page).code.locator('.cm-line').first();

  await focusCode(page, 'start');
  await page.keyboard.press('ControlOrMeta+/');
  await expect(first).toHaveText('# import math');
  await page.keyboard.press('ControlOrMeta+/');
  await expect(first).toHaveText('import math');
});

test('Shift+Alt+F formats the code in Ruff’s style', async ({ page, isMobile }) => {
  test.skip(isMobile, shortcuts);
  await openGallery(page);
  const { code } = editor(page);

  await focusCode(page);
  await page.keyboard.type('\nx=[1,2]');
  await page.keyboard.press('Shift+Alt+F');

  await expect(code.locator('.cm-line', { hasText: 'x = [1, 2]' })).toBeVisible();
});

test('Tab indents the code, and Escape then Tab leaves the editor', async ({ page, isMobile }) => {
  test.skip(isMobile, shortcuts);
  await openGallery(page);
  const { code } = editor(page);

  await focusCode(page);
  await page.keyboard.press('Tab');
  // toHaveText would trim the spaces away, so the line's text is read as it is.
  await expect.poll(() => code.locator('.cm-line').last().textContent()).toBe('    ');
  await page.keyboard.press('Escape');
  await page.keyboard.press('Tab');

  await expect(code).not.toBeFocused();
});

test("choosing an editor theme in the top bar's panel repaints every editor", async ({ page }) => {
  await openGallery(page);
  const editors = editor(page).section.locator('.cm-editor');
  await expect(editors).toHaveCount(5);

  await page.getByRole('button', { name: 'Theme', exact: true }).click();
  await page.getByRole('radio', { name: 'Dracula' }).check();

  for (const each of await editors.all()) {
    await expect(each).toHaveCSS('background-color', 'rgb(40, 42, 54)');
  }
});

test('a read-only editor can be read but not changed, in each language', async ({ page }) => {
  await openGallery(page);
  const solutions = editor(page).section.getByRole('textbox', { name: 'Solution' });
  await expect(solutions).toHaveCount(4);

  for (const solution of await solutions.all()) {
    const before = await solution.textContent();
    await solution.click();
    await page.keyboard.type('x');
    await expect(solution).toHaveText(before ?? '');
  }
});

test('the gallery fits the screen without scrolling sideways', async ({ page }) => {
  await openGallery(page);
  const width = await page.evaluate(() => document.documentElement.scrollWidth);

  expect(width).toBeLessThanOrEqual(page.viewportSize()?.width ?? 0);
});
