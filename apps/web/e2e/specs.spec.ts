import { expect, type Page, test } from '@playwright/test';
import { criterion, type HeldCriterion, type HeldSpec, spec, standInSpecs } from './specs';
import { signedIn, standIn } from './supabase';
import { acme, ada, ben, member, type Role, standInTeam, team } from './workspaces';

// A workspace's specs and their acceptance criteria (decision record 49).

const retry = spec(acme, 3, 'Retry failed payments', {
  status: 'in_review',
  body: '## Context\n\nCards fail at random.',
});
const retryCriteria = [
  criterion(retry, 1, 'When a payment fails, the system shall retry it once after 30 seconds'),
  criterion(retry, 2, 'The retry uses the same idempotency key'),
];

/** Signed in as Ada, with the given role in Acme, where Ben is an owner. */
async function inAcme(
  page: Page,
  role: Role,
  writing: { specs?: HeldSpec[]; criteria?: HeldCriterion[] } = {},
) {
  await standIn(page);
  await standInTeam(
    page,
    team({ workspaces: [acme], members: [member(acme, ada, role), member(acme, ben, 'owner')] }),
  );
  const calls = await standInSpecs(page, writing);
  await signedIn(page);
  return calls;
}

test('a workspace with no specs says what one is, and a member writes the first', async ({
  page,
}) => {
  const calls = await inAcme(page, 'member');

  await page.goto('/app/acme/specs');
  await expect(page.getByRole('region', { name: 'No specs yet' })).toContainText('SPEC-1/AC-1');
  await page.getByRole('button', { name: 'Write the first spec' }).click();
  const dialog = page.getByRole('dialog', { name: 'New spec' });
  await dialog.getByRole('button', { name: 'Create spec' }).click();
  await expect(dialog.getByText('Give the spec a title.')).toBeVisible();
  await expect(dialog.getByText('Write what must be true.')).toBeVisible();

  await dialog.getByLabel('Title').fill('Retry failed payments');
  await dialog
    .getByLabel('First acceptance criterion')
    .fill('When a payment fails, the system shall retry it once after 30 seconds');
  await dialog.getByRole('button', { name: 'Create spec' }).click();

  await expect(page).toHaveURL(/\/app\/acme\/SPEC-1$/);
  await expect(page).toHaveTitle('SPEC-1 Retry failed payments · Acme · Sulba');
  await expect(page.getByText('SPEC-1/AC-1', { exact: true })).toBeVisible();
  await expect(page.getByRole('region', { name: 'History' })).toContainText(
    'Ada Lovelace added SPEC-1/AC-1',
  );
  expect(calls.rpc).toEqual([
    {
      name: 'create_spec',
      args: {
        workspace: acme.id,
        title: 'Retry failed payments',
        criteria: ['When a payment fails, the system shall retry it once after 30 seconds'],
      },
    },
  ]);
});

test('the list shows each spec’s ID, status, criteria and owner, newest first', async ({
  page,
}) => {
  const export_ = spec(acme, 4, 'Export invoices', { ownerId: null });
  await inAcme(page, 'viewer', { specs: [retry, export_], criteria: retryCriteria });

  await page.goto('/app/acme/specs');
  const rows = page.getByRole('row');
  await expect(rows.nth(1)).toContainText('SPEC-4');
  await expect(rows.nth(1)).toContainText('Export invoices');
  await expect(rows.nth(1)).toContainText('No owner');
  await expect(rows.nth(2)).toContainText('SPEC-3');
  await expect(rows.nth(2)).toContainText('In review');
  await expect(rows.nth(2).getByRole('cell').nth(3)).toHaveText('2');
  await expect(rows.nth(2)).toContainText('Ada Lovelace');
  await expect(page.getByRole('button', { name: 'New spec' })).toHaveCount(0);

  await page.getByRole('link', { name: 'Retry failed payments' }).click();
  await expect(page).toHaveURL(/\/app\/acme\/SPEC-3$/);
});

test('a member adds, rewords and removes criteria, and a removed number isn’t given again', async ({
  page,
}) => {
  const calls = await inAcme(page, 'member', { specs: [retry], criteria: [...retryCriteria] });

  await page.goto('/app/acme/SPEC-3');
  await page.getByLabel('New criterion').fill('Retries show on the invoice');
  await page.getByRole('button', { name: 'Add criterion' }).click();
  await expect(page.getByText('SPEC-3/AC-3', { exact: true })).toBeVisible();

  await page.getByRole('button', { name: /^Edit SPEC-3\/AC-1/ }).click();
  const wording = page.getByRole('textbox', { name: 'SPEC-3/AC-1’s wording' });
  await wording.fill('When a payment fails, the system shall retry it once after 60 seconds');
  await wording.press('Enter');
  await expect(
    page.getByRole('button', { name: /^Edit SPEC-3\/AC-1: .*60 seconds$/ }),
  ).toBeVisible();
  expect(calls.patches).toContainEqual({
    table: 'criteria',
    body: { text: 'When a payment fails, the system shall retry it once after 60 seconds' },
  });

  await page.getByRole('button', { name: /^Edit SPEC-3\/AC-2/ }).click();
  await page.getByRole('textbox', { name: 'SPEC-3/AC-2’s wording' }).fill('Changed my mind');
  await page.getByRole('textbox', { name: 'SPEC-3/AC-2’s wording' }).press('Escape');
  await expect(
    page.getByRole('button', { name: /^Edit SPEC-3\/AC-2: The retry uses/ }),
  ).toBeVisible();

  const third = page.getByRole('listitem').filter({ hasText: 'SPEC-3/AC-3' });
  await third.getByRole('button', { name: 'Remove' }).click();
  const confirm = page.getByRole('dialog', { name: 'Remove SPEC-3/AC-3?' });
  await confirm.getByRole('button', { name: 'Remove' }).click();
  await expect(page.getByText('SPEC-3/AC-3', { exact: true })).toHaveCount(0);

  await page.getByLabel('New criterion').fill('Retries are logged');
  await page.getByRole('button', { name: 'Add criterion' }).click();
  await expect(page.getByText('SPEC-3/AC-4', { exact: true })).toBeVisible();
  await expect(page.getByRole('region', { name: 'History' })).toContainText('removed SPEC-3/AC-3');
});

test('a member changes the status and owner, renames the spec, and the history says so', async ({
  page,
}) => {
  const calls = await inAcme(page, 'member', { specs: [retry], criteria: [...retryCriteria] });

  await page.goto('/app/acme/SPEC-3');
  await page.getByRole('button', { name: 'Status' }).click();
  await page.getByRole('option', { name: /^Approved/ }).click();
  await page.getByRole('button', { name: 'Owner' }).click();
  await page.getByRole('option', { name: 'Ben Ortiz' }).click();
  const title = page.getByRole('textbox', { name: 'Title' });
  await title.fill('Retry a failed payment');
  await title.press('Enter');

  const history = page.getByRole('region', { name: 'History' });
  await expect(history).toContainText('Ada Lovelace moved it to Approved');
  await expect(history).toContainText('Ada Lovelace gave it to Ben Ortiz');
  await expect(history).toContainText('Ada Lovelace renamed it “Retry a failed payment”');
  expect(calls.patches.map(({ body }) => body)).toEqual([
    { status: 'approved' },
    { owner_id: ben.id },
    { title: 'Retry a failed payment' },
  ]);
});

test('a spec’s text saves a moment after the writer stops typing', async ({ page }) => {
  const calls = await inAcme(page, 'member', { specs: [retry], criteria: [...retryCriteria] });

  await page.goto('/app/acme/SPEC-3');
  const text = page.getByRole('textbox', { name: 'SPEC-3’s text' });
  await expect(text).toContainText('Cards fail at random.');
  await text.click();
  await page.keyboard.press('ControlOrMeta+End');
  await page.keyboard.type(' Most succeed a minute later.');
  await expect(page.getByText('Saved', { exact: true })).toBeVisible();
  await expect
    .poll(() => calls.patches.filter(({ table }) => table === 'specs').at(-1)?.body)
    .toEqual({ body: '## Context\n\nCards fail at random. Most succeed a minute later.' });
});

test('a viewer reads a spec and changes nothing', async ({ page }) => {
  await inAcme(page, 'viewer', { specs: [retry], criteria: retryCriteria });

  await page.goto('/app/acme/SPEC-3');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Retry failed payments');
  await expect(page.getByRole('textbox', { name: 'Title' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Status' })).toHaveCount(0);
  await expect(page.getByLabel('New criterion')).toHaveCount(0);
  await expect(page.getByRole('button', { name: /^Edit SPEC-3/ })).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'SPEC-3’s text' })).toHaveAttribute(
    'contenteditable',
    'false',
  );
  await expect(page.getByRole('complementary', { name: 'Details' })).toContainText('In review');
});

test('an address with no spec says so', async ({ page }) => {
  await inAcme(page, 'member', { specs: [retry] });

  await page.goto('/app/acme/SPEC-99');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('No spec here');
  await expect(page.getByText('SPEC-99 hasn’t been written in this workspace.')).toBeVisible();

  await page.goto('/app/acme/SPEC-x');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('No spec here');
  await page.getByRole('link', { name: 'Go to the specs' }).click();
  await expect(page).toHaveURL(/\/app\/acme\/specs$/);
});
