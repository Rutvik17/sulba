import AxeBuilder from '@axe-core/playwright';
import { expect, type Page, test } from '@playwright/test';
import { islandsHydrated } from './islands';

const wcag = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

/** The fixture lab's Catch stage, with the two stages before it done (lab.spec.ts). */
async function openReview(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('sulba:passed:stg_demo01', '1');
    localStorage.setItem('sulba:passed:stg_demo02', '1');
    localStorage.setItem(
      'sulba:code:stg_demo02',
      'def count(choices, choice):\n    return sum(1 for each in choices if each == choice)\n\n\ndef share(choices, choice):\n    return count(choices, choice) / len(choices)\n',
    );
  });
  await page.goto('/demo/counting/tallies/?stage=check');
  await expect(page.getByRole('textbox', { name: 'report.py', exact: true })).toBeVisible();
}

/** The fixture lab's Ship stage, with the three stages before it done (lab.spec.ts). */
async function openShip(page: Page) {
  await page.addInitScript(() => {
    for (const stage of ['stg_demo01', 'stg_demo02', 'stg_demo03']) {
      localStorage.setItem(`sulba:passed:${stage}`, '1');
    }
  });
  await page.goto('/demo/counting/tallies/?stage=ship');
  await expect(page.getByRole('textbox', { name: 'report.py', exact: true })).toBeVisible();
}

for (const scheme of ['dark', 'light'] as const) {
  for (const path of [
    '/',
    '/about/',
    '/contact/',
    '/privacy/',
    '/terms/',
    '/no-such-page/',
    '/gallery/',
  ]) {
    test(`${path} has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(path);

      const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

      expect(results.violations).toEqual([]);
    });
  }

  test(`the contact form's messages have no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    // Turnstile starts loading when the form is first used; no test reaches Cloudflare.
    await page.route('https://challenges.cloudflare.com/**', (route) => route.abort());
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/contact/');
    await page.getByRole('button', { name: 'Send' }).click();
    await expect(page.getByLabel('Name')).toHaveAttribute('aria-invalid', 'true');

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`the open theme panel has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/');
    await page.getByRole('button', { name: 'Theme' }).click();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  for (const [what, trigger, role] of [
    ['side panel', 'Open the review', 'dialog'],
    ['menu', 'Session', 'menu'],
  ] as const) {
    test(`the gallery's open ${what} has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
      page,
    }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto('/gallery/');
      await islandsHydrated(page);
      await page.getByRole('button', { name: trigger }).click();
      await expect(page.getByRole(role)).toBeVisible();
      // React Aria marks an overlay data-entering until it has finished sliding or fading in.
      await expect(page.locator('[data-entering]')).toHaveCount(0);

      const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

      expect(results.violations).toEqual([]);
    });
  }

  test(`a lab page, with a run's results, has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    // The fixture course's lab (playwright.config.ts).
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/demo/counting/tallies/');
    await page.getByRole('button', { name: 'Run tests' }).click();
    // The first run waits for Python to load.
    await expect(page.getByText('0 of 2 tests passed.')).toBeVisible({ timeout: 60_000 });

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a stage's chart has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    // The chart draws the learner's code, so the stage needs code that passes.
    await page.addInitScript(() => {
      localStorage.setItem('sulba:passed:stg_demo01', '1');
      localStorage.setItem('sulba:passed:stg_demo02', '1');
      localStorage.setItem(
        'sulba:code:stg_demo02',
        'def count(choices, choice):\n    return sum(1 for each in choices if each == choice)\n\n\ndef share(choices, choice):\n    return count(choices, choice) / len(choices)\n',
      );
    });
    await page.goto('/demo/counting/tallies/?stage=share');
    await page.getByRole('tab', { name: 'Chart' }).click();
    // The chart is drawn once Python has loaded.
    await expect(page.getByRole('img', { name: /share of yes votes/ })).toBeVisible({
      timeout: 60_000,
    });

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a Catch stage about to finish its review has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await openReview(page);
    await page.getByRole('button', { name: 'Run tests' }).click();
    await expect(page.getByText('0 of 2 production checks passed.', { exact: false })).toBeVisible({
      timeout: 60_000,
    });
    await page.getByRole('button', { name: 'Finish review' }).click();
    await expect(page.getByRole('button', { name: 'Keep reviewing' })).toBeVisible();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a finished Catch review has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.addInitScript(() =>
      localStorage.setItem('sulba:review:stg_demo03', '{"caught":["tst_demo07"],"total":2}'),
    );
    await openReview(page);
    await page.getByRole('button', { name: 'Run tests' }).click();
    await expect(page.getByText('0 of 2 production checks passed.', { exact: false })).toBeVisible({
      timeout: 60_000,
    });
    await page.getByRole('button', { name: 'See each problem' }).click();
    await expect(page.getByText('Missed', { exact: true })).toBeVisible();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a Ship stage's results have no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await openShip(page);
    await page.getByRole('button', { name: 'Run tests' }).click();
    await expect(page.getByText('0 of 2 checks passed.', { exact: false })).toBeVisible({
      timeout: 60_000,
    });

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a lab's explanation, with its formulas, has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/demo/counting/tallies/');
    await page.getByRole('tab', { name: 'Explanation' }).click();
    await expect(page.locator('math[display="block"]')).toBeVisible();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });
}
