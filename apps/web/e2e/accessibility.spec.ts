import AxeBuilder from '@axe-core/playwright';
import { expect, type Page, test } from '@playwright/test';
import { islandsHydrated } from './islands';
import { criterion, spec, standInSpecs } from './specs';
import { signedIn, standIn, supabase } from './supabase';
import { acme, ada, ben, link, member, standInTeam, team } from './workspaces';

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
  await page.goto('/academy/demo/counting/tallies/?stage=check');
  await expect(page.getByRole('textbox', { name: 'report.py', exact: true })).toBeVisible();
}

/** The fixture lab's Ship stage, with the three stages before it done (lab.spec.ts). */
async function openShip(page: Page) {
  await page.addInitScript(() => {
    for (const stage of ['stg_demo01', 'stg_demo02', 'stg_demo03']) {
      localStorage.setItem(`sulba:passed:${stage}`, '1');
    }
  });
  await page.goto('/academy/demo/counting/tallies/?stage=ship');
  await expect(page.getByRole('textbox', { name: 'report.py', exact: true })).toBeVisible();
}

for (const scheme of ['dark', 'light'] as const) {
  for (const path of [
    '/academy/',
    '/about/',
    '/contact/',
    '/privacy/',
    '/terms/',
    '/sign-in/',
    '/account/',
    '/academy/review/',
    '/academy/demo/',
    '/no-such-page/',
    '/gallery/',
  ]) {
    test(`${path} has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({ page }) => {
      await page.route(`${supabase}/**`, (route) => route.abort());
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(path);

      const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

      expect(results.violations).toEqual([]);
    });
  }

  test(`the account page, signed in with days studied, has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.clock.setFixedTime(new Date('2026-10-14T12:00:00'));
    await standIn(page, {
      studyDays: [
        { day: '2026-10-01', seconds: 1500 },
        { day: '2026-10-13', seconds: 600 },
        { day: '2026-10-14', seconds: 300 },
      ],
    });
    await signedIn(page);
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/account/');
    await expect(page.getByText('You studied on 3 of the last 84 days.')).toBeVisible();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  for (const [path, heading] of [
    ['/app/acme/specs', 'Specs'],
    ['/app/acme/SPEC-3', 'Retry failed payments'],
    ['/app/acme/members', 'Members'],
    ['/app/acme/settings', 'Settings'],
    ['/app/new', 'Create a workspace'],
  ] as const) {
    test(`the app's ${path} has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
      page,
    }) => {
      await standIn(page);
      await standInTeam(
        page,
        team({
          workspaces: [acme],
          members: [member(acme, ada, 'owner'), member(acme, ben, 'member')],
          invitations: [link(acme, 'd'.repeat(64))],
        }),
      );
      const written = spec(acme, 3, 'Retry failed payments', { body: '## Context\n\nCards fail.' });
      await standInSpecs(page, {
        specs: [written],
        criteria: [criterion(written, 1, 'When a payment fails, the system shall retry it once')],
      });
      await signedIn(page);
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(path);
      await expect(page.getByRole('heading', { level: 1, name: heading })).toBeAttached();

      const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

      expect(results.violations).toEqual([]);
    });
  }

  test(`a course page with a lab's stages done has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.addInitScript(() => localStorage.setItem('sulba:passed:stg_demo01', '1'));
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/academy/demo/');
    // Every module open, so its labs are checked too.
    for (const level of ['First', 'Second']) {
      await page
        .getByRole('region', { name: level })
        .getByRole('button', { name: 'Show all modules' })
        .click();
    }
    await expect(page.getByText('1 of 4 stages done').last()).toBeVisible();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a review card, with its answer and history, has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem('sulba:passed:stg_demo01', '1');
      localStorage.setItem(
        'sulba:reviews',
        JSON.stringify([
          {
            id: '10000000-0000-4000-8000-000000000001',
            card_id: 'crd_demo02',
            rating: 4,
            reviewed_at: '2026-10-01T09:00:00.000Z',
          },
        ]),
      );
    });
    await page.clock.setFixedTime(new Date('2026-10-15T09:00:00Z'));
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/academy/review/');
    await page.getByRole('button', { name: 'Show answer' }).click();
    await page.getByText('History').click();
    await expect(page.locator('[data-history-list] li')).toHaveCount(1);

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

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
    await page.goto('/academy/');
    await page.getByRole('button', { name: 'Theme' }).click();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`the theme panel with the editor themes has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/academy/demo/counting/tallies/');
    await expect(page.getByRole('textbox', { name: 'tally.py', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Theme', exact: true }).click();

    // Each sample shows a theme in its own colours, which some themes make faint for comments, as
    // the editor then does. Screen readers skip the sample; the theme's name labels the choice.
    const results = await new AxeBuilder({ page })
      .withTags(wcag)
      .exclude('[data-sample]')
      .analyze();

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
    await page.goto('/academy/demo/counting/tallies/');
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
    await page.goto('/academy/demo/counting/tallies/?stage=share');
    await page.getByRole('tab', { name: 'Chart' }).click();
    // The chart is drawn once Python has loaded.
    await expect(page.getByRole('img', { name: /share of yes votes/ })).toBeVisible({
      timeout: 60_000,
    });

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`an explanation with a formula wider than its panel has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.addInitScript(() => localStorage.setItem('sulba:passed:stg_demo01', '1'));
    await page.goto('/academy/demo/counting/tallies/?stage=share');
    await page.getByRole('tab', { name: 'Explanation' }).click();
    await expect(page.locator('[data-scroll]')).toHaveAttribute('tabindex', '0');

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

  test(`a lab that runs on the learner's machine, with a stage done there, has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.addInitScript(() => localStorage.setItem('sulba:passed:stg_demo06', '1'));
    await page.goto('/academy/demo/ledgers/ledger/?stage=balance');
    await expect(page.getByText('Stage 1 done.')).toBeVisible();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a Problem stage, with its plan being written, has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/academy/demo/interviews/pairs/');
    await page.getByRole('button', { name: 'Start' }).click();
    await expect(page.getByRole('textbox', { name: 'Your plan' })).toBeVisible();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a Problem stage past its minutes, with its plan open, has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.addInitScript(() => {
      const state = { started: Date.now() - 21 * 60_000, plan: 'A dict of the numbers seen.' };
      localStorage.setItem(
        'sulba:problem:stg_demo05',
        JSON.stringify({ ...state, coding: true, solved: null }),
      );
    });
    await page.goto('/academy/demo/interviews/pairs/');
    await page.getByRole('tab', { name: 'Plan', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'Your plan' })).toBeVisible();
    await expect(page.getByRole('timer')).toHaveText(/^21:0\d of 20:00$/);

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a Design stage, with its rubric being marked, has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.addInitScript(() => {
      const state = { started: Date.now() - 26 * 60_000, attempts: 1, design: 'One table.' };
      localStorage.setItem(
        'sulba:design:stg_demo10',
        JSON.stringify({
          ...state,
          handedIn: true,
          answers: ['Count it again.', 'The table.'],
          answered: 25 * 60,
          marks: [true, false, false],
          marked: false,
        }),
      );
    });
    await page.goto('/academy/demo/interviews/poll-design/');
    await expect(page.getByRole('heading', { name: 'Rubric' })).toBeVisible();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });

  test(`a lab's explanation, with its formulas, has no WCAG 2.2 AA violations in the ${scheme} theme`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto('/academy/demo/counting/tallies/');
    await page.getByRole('tab', { name: 'Explanation' }).click();
    await expect(page.locator('math[display="block"]')).toBeVisible();

    const results = await new AxeBuilder({ page }).withTags(wcag).analyze();

    expect(results.violations).toEqual([]);
  });
}
