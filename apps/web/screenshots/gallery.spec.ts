import { expect, type Page, test } from '@playwright/test';

/**
 * Each gallery section, and how a desktop test shows its transient states: one control with
 * keyboard focus and the pointer over another, so a single picture holds both.
 */
const sections: { id: string; name: string; states: (page: Page) => Promise<void> }[] = [
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
];

/** The overlays, pictured open: the side panel, and the menu with its first item focused. */
const overlays = [
  { id: 'panel', trigger: 'Open the review', role: 'dialog', keys: [] },
  { id: 'menu', trigger: 'Session', role: 'menu', keys: ['ArrowDown'] },
] as const;

for (const { id, name, states } of sections) {
  for (const scheme of ['dark', 'light'] as const) {
    test(`${name} in the ${scheme} theme`, async ({ page, isMobile }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto('/gallery/');
      await expect(page.locator('astro-island[ssr]')).toHaveCount(0);
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
      await expect(page.locator('astro-island[ssr]')).toHaveCount(0);
      await page.getByRole('button', { name: trigger }).click();
      for (const key of keys) await page.keyboard.press(key);

      // The element that holds the overlay's edge: the panel or the menu's card.
      const overlay = page.getByRole(role).locator('xpath=..');
      await expect(overlay).toHaveScreenshot(`${id}-${scheme}.png`);
    });
  }
}
