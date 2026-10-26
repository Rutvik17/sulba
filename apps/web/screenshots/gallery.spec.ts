import { expect, type Page, test } from '@playwright/test';
import { islandsHydrated } from '../e2e/islands';

/** Whether a code editor's last line number sits level with its last line. */
function numbered(editor: Element) {
  const top = (nodes: NodeListOf<Element>) =>
    Array.from(nodes).at(-1)?.getBoundingClientRect().top ?? Number.NaN;
  const numbers = top(editor.querySelectorAll('.cm-lineNumbers .cm-gutterElement'));
  return Math.abs(numbers - top(editor.querySelectorAll('.cm-line'))) < 1;
}

/**
 * Each gallery section, and how a desktop test shows its transient states: one control with
 * keyboard focus and the pointer over another, so a single picture holds both. `ready` waits for
 * anything that draws after React takes over.
 */
const sections: {
  id: string;
  name: string;
  states: (page: Page) => Promise<void>;
  ready?: (page: Page) => Promise<void>;
}[] = [
  {
    id: 'button',
    name: 'Button',
    states: async (page) => {
      await page.getByRole('button', { name: 'Show a hint' }).first().focus();
      await page.keyboard.press('Shift+Tab');
      await page.keyboard.press('Tab');
      await page.getByRole('button', { name: 'Run tests' }).first().hover();
    },
  },
  {
    id: 'segmented',
    name: 'Segmented choice',
    states: async (page) => {
      await page.getByRole('radiogroup', { name: 'Where tests run' }).getByText('Browser').click();
      await page.keyboard.press('ArrowRight');
      await page.getByRole('radiogroup', { name: 'Layout' }).getByText('Editor').hover();
    },
  },
  {
    id: 'tabs',
    name: 'Tabs',
    states: async (page) => {
      await page.getByRole('tab', { name: 'Brief' }).click();
      await page.keyboard.press('ArrowRight');
      await page.getByRole('tab', { name: 'Tests' }).hover();
    },
  },
  {
    id: 'slider',
    name: 'Slider',
    states: async (page) => {
      await page.getByRole('slider', { name: 'Learning rate' }).focus();
      await page.keyboard.press('ArrowRight');
      await page.keyboard.press('Tab');
    },
  },
  {
    id: 'formulas',
    name: 'Formulas',
    // The math font loads once a formula is on screen; the picture waits for it.
    ready: async (page) => {
      await page.getByRole('region', { name: 'Formulas' }).scrollIntoViewIfNeeded();
      // Astro adds a hash to each family's name.
      const loaded = () =>
        page.evaluate(() =>
          [...document.fonts].some(
            (face) => face.family.includes('Noto Sans Math') && face.status === 'loaded',
          ),
        );
      await expect.poll(loaded).toBe(true);
    },
    states: async () => {},
  },
  {
    id: 'editor',
    name: 'Code editor',
    // Ruff's marks come from a Web Worker. An editor measures its lines only once it's on screen,
    // and places its line numbers by those heights, so on a phone, where the section starts below
    // the window, each editor is brought into view until its numbers line up.
    ready: async (page) => {
      await expect(page.locator('.cm-lintRange-error')).toHaveText('bias');
      for (const editor of await page.locator('.cm-editor').all()) {
        await editor.scrollIntoViewIfNeeded();
        await expect.poll(() => editor.evaluate(numbered)).toBe(true);
      }
    },
    states: async () => {},
  },
  {
    id: 'chart',
    name: 'Chart',
    states: async () => {},
  },
];

/** The overlays, pictured open: the side panel, and the menu with its first item focused. */
const overlays = [
  { id: 'panel', trigger: 'Open the review', role: 'dialog', keys: [] },
  { id: 'menu', trigger: 'Session', role: 'menu', keys: ['ArrowDown'] },
] as const;

for (const { id, name, states, ready } of sections) {
  for (const scheme of ['dark', 'light'] as const) {
    test(`${name} in the ${scheme} theme`, async ({ page, isMobile }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto('/gallery/');
      await islandsHydrated(page);
      await ready?.(page);
      if (!isMobile) await states(page);

      await expect(page.getByRole('region', { name })).toHaveScreenshot(`${id}-${scheme}.png`);
    });
  }
}

for (const { id, trigger, role, keys } of overlays) {
  for (const scheme of ['dark', 'light'] as const) {
    test(`the open ${id} in the ${scheme} theme`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto('/gallery/');
      await islandsHydrated(page);
      await page.getByRole('button', { name: trigger }).click();
      for (const key of keys) await page.keyboard.press(key);

      // The element that holds the overlay's edge: the panel or the menu's card.
      const overlay = page.getByRole(role).locator('xpath=..');
      await expect(overlay).toHaveScreenshot(`${id}-${scheme}.png`);
    });
  }
}

// The top bar's theme panel, open, with the editor themes the gallery's editor takes: one has
// keyboard focus and the pointer is over another.
for (const scheme of ['dark', 'light'] as const) {
  test(`the open theme panel in the ${scheme} theme`, async ({ page, isMobile }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/gallery/');
    await islandsHydrated(page);
    await page.getByRole('button', { name: 'Theme', exact: true }).click();
    if (!isMobile) {
      await page.getByRole('radio', { name: 'Sulba' }).focus();
      await page.keyboard.press('Shift+Tab');
      await page.keyboard.press('Tab');
      await page.getByRole('radio', { name: 'Light Modern' }).hover();
    }

    await expect(page.locator('#theme-panel')).toHaveScreenshot(`theme-panel-${scheme}.png`);
  });
}
