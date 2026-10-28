import { expect, type Page, test } from '@playwright/test';
import { type Evidence, type HeldProof, repository, sha, standInEvidence } from './evidence';
import { criterion, spec, standInSpecs } from './specs';
import { signedIn, standIn } from './supabase';
import { acme, ada, ben, member, type Role, standInTeam, team } from './workspaces';

// What a workspace's CI proves about its criteria (decision record 50).

const retry = spec(acme, 3, 'Retry failed payments', { status: 'approved' });
const criteria = [
  criterion(retry, 1, 'When a payment fails, the system shall retry it once after 30 seconds'),
  criterion(retry, 2, 'The retry uses the same idempotency key'),
  criterion(retry, 3, 'Each retry is logged'),
];
const of = { id: retry.id, number: retry.number, title: retry.title };
const proof = (n: number, counts: Partial<HeldProof> = {}): HeldProof => ({
  criterion: criteria[n - 1]?.id ?? '',
  spec: of,
  number: n,
  text: criteria[n - 1]?.text ?? '',
  passed: 0,
  failed: 0,
  skipped: 0,
  suspectSince: null,
  ...counts,
});

const payments = repository(acme, 'acme-co/payments');
const evidence: Partial<Evidence> = {
  repositories: [payments],
  reports: [
    {
      id: 'r1',
      repository: payments.name,
      suite: 'unit',
      sha,
      runId: 1000,
      tests: 412,
      passed: 401,
      failed: 3,
      skipped: 8,
    },
  ],
  proofs: [proof(1, { passed: 1 }), proof(2, { failed: 1 }), proof(3)],
  claims: [
    { spec: 3, criterion: 1, name: 'test_SPEC_3_AC_1_retries_once', outcome: 'passed' },
    {
      spec: 3,
      criterion: 2,
      name: 'test_SPEC_3_AC_2_keeps_the_key',
      outcome: 'failed',
      message: "assert 'k2' == 'k1'",
    },
  ],
};

/** Signed in as Ada, with the given role in Acme, where Ben is an owner. */
async function inAcme(page: Page, role: Role, held: Partial<Evidence> = {}) {
  await standIn(page);
  await standInTeam(
    page,
    team({ workspaces: [acme], members: [member(acme, ada, role), member(acme, ben, 'owner')] }),
  );
  await standInSpecs(page, { specs: [retry], criteria });
  const calls = await standInEvidence(page, acme, held);
  await signedIn(page);
  return calls;
}

test('a workspace with no repository says where evidence comes from, and an admin goes to add one', async ({
  page,
}) => {
  await inAcme(page, 'admin');

  await page.goto('/app/acme/evidence');
  await expect(page.getByRole('region', { name: 'No evidence yet' })).toContainText(
    'Evidence comes from your CI.',
  );
  await page.getByRole('link', { name: 'Add a repository' }).click();
  await expect(page).toHaveURL(/\/app\/acme\/settings#repositories$/);
});

test('a viewer is told who adds repositories', async ({ page }) => {
  await inAcme(page, 'viewer');

  await page.goto('/app/acme/evidence');
  await expect(page.getByRole('region', { name: 'No evidence yet' })).toContainText(
    'An admin or owner adds repositories in Settings.',
  );
  await page.goto('/app/acme/settings');
  await expect(page.getByRole('form', { name: 'Add a repository' })).toHaveCount(0);
});

test('an admin adds a repository, and Settings gives the step for its workflow', async ({
  page,
}) => {
  const calls = await inAcme(page, 'admin');

  await page.goto('/app/acme/settings');
  const name = page.getByRole('textbox', { name: 'Repository' });
  await name.fill('payments');
  await page.getByRole('button', { name: 'Add repository' }).click();
  await expect(page.getByText('Write it as owner/name, as GitHub shows it')).toBeVisible();
  await name.fill('acme-co/payments');
  await page.getByRole('button', { name: 'Add repository' }).click();
  await expect(page.getByRole('cell', { name: 'acme-co/payments' })).toBeVisible();
  expect(calls.rpc).toEqual([
    {
      name: 'add_repository',
      args: { workspace: acme.id, name: 'acme-co/payments', branch: 'main' },
    },
  ]);

  await name.fill('Acme-Co/Payments');
  await page.getByRole('button', { name: 'Add repository' }).click();
  await expect(page.getByRole('alert')).toHaveText('This workspace already has that repository.');

  const steps = page.getByRole('region', { name: 'Sending test results' });
  await expect(steps).toContainText('id-token: write');
  await expect(steps).toContainText('pytest --junit-xml=junit.xml');
  await expect(steps).toContainText('audience=https%3A%2F%2Fsulba.dev');
  await expect(steps).toContainText('/api/results?workspace=acme&suite=tests');
  await page.getByRole('button', { name: 'Test runner' }).click();
  await page.getByRole('option', { name: 'Maven' }).click();
  await page.getByRole('textbox', { name: 'Suite' }).fill('integration');
  await expect(steps).toContainText('target/surefire-reports/TEST-*.xml');
  await expect(steps).toContainText('suite=integration');
});

test('an admin changes a repository’s branch and removes it', async ({ page }) => {
  const calls = await inAcme(page, 'owner', evidence);

  await page.goto('/app/acme/settings');
  await page.getByRole('button', { name: 'Change branch' }).click();
  const dialog = page.getByRole('dialog', { name: 'acme-co/payments’s branch' });
  await dialog.getByRole('textbox', { name: 'Branch' }).fill('trunk');
  await dialog.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('cell', { name: 'trunk' })).toBeVisible();
  expect(calls.patches).toEqual([{ branch: 'trunk' }]);

  await page.getByRole('button', { name: 'Remove' }).click();
  await page
    .getByRole('dialog', { name: 'Remove acme-co/payments?' })
    .getByRole('button', { name: 'Remove' })
    .click();
  await expect(page.getByRole('cell', { name: 'acme-co/payments' })).toHaveCount(0);
  expect(calls.deleted).toEqual(['acme-co/payments']);
});

test('the evidence lists failing criteria first, then unproven, then proven, with each run', async ({
  page,
}) => {
  await inAcme(page, 'viewer', evidence);

  await page.goto('/app/acme/evidence');
  await expect(page.getByText('3 criteria: 1 failing, 1 unproven, 1 proven')).toBeVisible();
  const rows = page.getByRole('region', { name: 'Criteria' }).getByRole('row');
  await expect(rows.nth(1)).toContainText('SPEC-3/AC-2');
  await expect(rows.nth(1)).toContainText('Failing');
  await expect(rows.nth(1)).toContainText('1 failed');
  await expect(rows.nth(2)).toContainText('SPEC-3/AC-3');
  await expect(rows.nth(2)).toContainText('Unproven');
  await expect(rows.nth(2)).toContainText('None');
  await expect(rows.nth(3)).toContainText('SPEC-3/AC-1');
  await expect(rows.nth(3)).toContainText('Proven');

  const runs = page.getByRole('region', { name: 'Runs' });
  await expect(runs).toContainText('412 tests: 401 passed, 3 failed, 8 skipped');
  await expect(runs.getByRole('link', { name: 'a1b2c3d' })).toHaveAttribute(
    'href',
    `https://github.com/acme-co/payments/commit/${sha}`,
  );
  await expect(runs.getByRole('link', { name: 'CI, run 1000' })).toHaveAttribute(
    'href',
    'https://github.com/acme-co/payments/actions/runs/1000',
  );

  await page.getByRole('link', { name: 'SPEC-3/AC-2' }).click();
  await expect(page).toHaveURL(/\/app\/acme\/SPEC-3#AC-2$/);
});

test('a spec’s criteria show their proof and the tests that name them', async ({ page }) => {
  await inAcme(page, 'viewer', evidence);

  await page.goto('/app/acme/specs');
  await expect(page.getByRole('row').nth(1)).toContainText('1 failing');

  await page.goto('/app/acme/SPEC-3');
  const failing = page.locator('#AC-2');
  await expect(failing).toContainText('Failing');
  // A failing criterion's tests are open, with what the failure said.
  await expect(failing).toContainText('test_SPEC_3_AC_2_keeps_the_key');
  await expect(failing).toContainText("assert 'k2' == 'k1'");
  await expect(page.locator('#AC-1')).toContainText('Proven');
  await expect(page.locator('#AC-1').getByText('test_SPEC_3_AC_1_retries_once')).toBeHidden();
  await page.locator('#AC-1').getByText('1 test').click();
  await expect(page.locator('#AC-1').getByText('test_SPEC_3_AC_1_retries_once')).toBeVisible();
  await expect(page.locator('#AC-3')).toContainText('Unproven');
});

test('a criterion reworded since its tests ran is unproven until a member confirms its tests', async ({
  page,
}) => {
  const calls = await inAcme(page, 'member', {
    ...evidence,
    proofs: [proof(1, { passed: 1, suspectSince: new Date().toISOString() }), proof(2), proof(3)],
  });

  await page.goto('/app/acme/SPEC-3');
  const reworded = page.locator('#AC-1');
  await expect(reworded).toContainText('Unproven');
  await expect(reworded).toContainText('SPEC-3/AC-1 was reworded after its tests ran');
  await reworded.getByRole('button', { name: 'Its tests check this wording' }).click();
  await expect(reworded).toContainText('Proven');
  await expect(reworded.getByRole('button', { name: 'Its tests check this wording' })).toHaveCount(
    0,
  );
  expect(calls.rpc).toEqual([{ name: 'confirm_criterion', args: { criterion: criteria[0]?.id } }]);
});

test('a viewer can’t confirm a reworded criterion’s tests', async ({ page }) => {
  await inAcme(page, 'viewer', {
    ...evidence,
    proofs: [proof(1, { passed: 1, suspectSince: new Date().toISOString() })],
  });

  await page.goto('/app/acme/SPEC-3');
  await expect(page.locator('#AC-1')).toContainText('was reworded after its tests ran');
  await expect(page.getByRole('button', { name: 'Its tests check this wording' })).toHaveCount(0);
});
