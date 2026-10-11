import { expect, type Page } from '@playwright/test';

/**
 * Waits until React has finished hydrating every island. Astro drops an island's ssr attribute as
 * soon as it hands the island to React, but React 19 hydrates in the background at low priority,
 * and a press or a key that lands before it finishes can be lost. React marks each element it has
 * taken over with a __reactProps key, and it finishes an element only after everything inside
 * it, so an island is done once each of its top-level elements has the mark.
 */
export async function islandsHydrated(page: Page) {
  await expect(page.locator('astro-island[ssr]')).toHaveCount(0);
  await page.waitForFunction(() =>
    [...document.querySelectorAll('astro-island')].every((island) =>
      [...island.children]
        .filter((child) => !['ASTRO-SLOT', 'TEMPLATE'].includes(child.tagName))
        .every((child) => Object.keys(child).some((key) => key.startsWith('__reactProps$'))),
    ),
  );
  // React commits the hydrated tree in the same task it finishes it; two frames make sure the
  // browser has run that task before the test goes on.
  await page.evaluate(
    () => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))),
  );
}
