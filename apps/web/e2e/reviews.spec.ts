import { expect, type Page, test } from '@playwright/test';
import { standInEvidence } from './evidence';
import { criterion, type HeldReview, type HeldSpec, review, spec, standInSpecs } from './specs';
import { signedIn, standIn } from './supabase';
import { acme, ada, ben, member, type Role, standInTeam, team } from './workspaces';

// A spec's reviewers, what they answer, and My work, which gathers what needs the person
// (decision record 52).

const retry = spec(acme, 3, 'Retry failed payments', { status: 'draft' });
const refunds = spec(acme, 4, 'Refund a payment', { status: 'in_review', ownerId: ben.id });
const criteria = [
  criterion(retry, 1, 'When a payment fails, the system shall retry it once after 30 seconds'),
  criterion(refunds, 1, 'A refund returns the whole amount'),
];

/** Signed in as Ada, with the given role in Acme, where Ben is an owner. */
async function inAcme(
  page: Page,
  role: Role,
  { specs = [retry, refunds], reviews = [] }: { specs?: HeldSpec[]; reviews?: HeldReview[] } = {},
) {
  await standIn(page);
  await standInTeam(
    page,
    team({ workspaces: [acme], members: [member(acme, ada, role), member(acme, ben, 'owner')] }),
  );
  const calls = await standInSpecs(page, { specs, criteria, reviews });
  await signedIn(page);
  return calls;
}

test('the owner asks Ben to review the spec, and its history says so', async ({ page }) => {
  const calls = await inAcme(page, 'member');

  await page.goto('/app/acme/SPEC-3');
  const details = page.getByRole('complementary', { name: 'Details' });
  await expect(details).toContainText('None');
  await details.getByRole('button', { name: 'Add reviewer' }).click();
  await expect(page.getByRole('menuitem')).toHaveText(['Ben Ortiz']);
  await page.getByRole('menuitem', { name: 'Ben Ortiz' }).click();

  await expect(details.getByRole('listitem')).toContainText(['Ben OrtizWaiting']);
  await expect(page.getByRole('region', { name: 'History' })).toContainText(
    'Ada Lovelace asked Ben Ortiz to review it',
  );
  expect(calls.rpc).toEqual([
    { name: 'request_review', args: { spec: retry.id, reviewer: ben.id } },
  ]);

  await details.getByRole('button', { name: 'Remove Ben Ortiz' }).click();
  await expect(details).toContainText('None');
  await expect(page.getByRole('region', { name: 'History' })).toContainText(
    'Ada Lovelace took Ben Ortiz off its reviewers',
  );
});

test('a spec with reviewers isn’t approved by hand, and an edit asks its approvers again', async ({
  page,
}) => {
  await inAcme(page, 'owner', {
    specs: [{ ...retry, status: 'in_review' }, refunds],
    reviews: [review(retry, ben, { verdict: 'approved', answeredAt: new Date().toISOString() })],
  });
  await page.goto('/app/acme/SPEC-3');
  const details = page.getByRole('complementary', { name: 'Details' });
  await expect(details.getByRole('listitem')).toContainText(['Ben OrtizApproved']);

  await page.getByRole('textbox', { name: 'Title' }).fill('Retry a failed payment');
  await page.getByRole('textbox', { name: 'Title' }).press('Enter');
  await expect(details.getByRole('listitem')).toContainText(['Ben OrtizWaiting']);
  await expect(details.getByRole('button', { name: 'Ask Ben Ortiz again' })).toHaveCount(0);

  await page.getByRole('button', { name: 'Status' }).click();
  await page.getByRole('option', { name: /^Approved/ }).click();
  await expect(page.getByRole('alert').first()).toHaveText(
    'Every reviewer has to approve the spec first.',
  );
});

test('a reviewer asks for changes with a note, then approves, which approves the spec', async ({
  page,
}) => {
  const calls = await inAcme(page, 'viewer', {
    reviews: [review(refunds, ada, { requestedBy: ben.id })],
  });

  await page.goto('/app/acme/SPEC-4');
  const yours = page.getByRole('region', { name: 'Your review' });
  await expect(yours).toContainText('Ben Ortiz asked you to review this spec.');
  await yours.getByRole('button', { name: 'Request changes' }).click();
  const dialog = page.getByRole('dialog', { name: 'Request changes to SPEC-4' });
  const send = dialog.getByRole('button', { name: 'Request changes' });
  await expect(send).toBeDisabled();
  await dialog
    .getByRole('textbox', { name: 'What should change?' })
    .fill('Say which fees it returns');
  await send.click();

  await expect(dialog).toBeHidden();
  const details = page.getByRole('complementary', { name: 'Details' });
  await expect(details.getByRole('listitem')).toContainText([
    'Ada LovelaceAsked for changesSay which fees it returns',
  ]);
  await expect(yours).toContainText('You asked for changes.');

  await yours.getByRole('button', { name: 'Approve' }).click();
  await expect(details).toContainText('Approved');
  await expect(yours).toBeHidden();
  expect(calls.rpc.map(({ args }) => args.verdict)).toEqual(['changes_requested', 'approved']);
  expect(calls.rpc[0]?.args.note).toBe('Say which fees it returns');
});

test('My work gathers the specs to review, the person’s own, and their failing criteria', async ({
  page,
}) => {
  await inAcme(page, 'member', {
    specs: [{ ...retry, status: 'in_review' }, refunds],
    reviews: [
      review(refunds, ada, { requestedBy: ben.id }),
      review(retry, ben, { verdict: 'approved', answeredAt: new Date().toISOString() }),
    ],
  });
  await standInEvidence(page, acme, {
    proofs: [
      {
        criterion: criteria[0]?.id ?? '',
        spec: { id: retry.id, number: 3, title: retry.title },
        number: 1,
        text: criteria[0]?.text ?? '',
        passed: 0,
        failed: 1,
        skipped: 0,
        suspectSince: null,
      },
    ],
  });

  await page.goto('/app/acme');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('My work');
  await expect(page.getByRole('link', { name: 'My work' })).toHaveAttribute('aria-current', 'page');
  await expect(
    page.getByText('1 spec to review, 1 spec of yours not yet built, 1 criterion failing'),
  ).toBeVisible();
  await expect(
    page.getByRole('region', { name: 'To review' }).getByRole('row').nth(1),
  ).toContainText('SPEC-4Refund a paymentBen Ortiz');
  await expect(
    page.getByRole('region', { name: 'Your specs' }).getByRole('row').nth(1),
  ).toContainText('SPEC-3Retry failed paymentsIn review1 of 1 approved');
  await expect(
    page.getByRole('region', { name: 'Failing on your specs' }).getByRole('row').nth(1),
  ).toContainText('SPEC-3/AC-1');

  await page.getByRole('link', { name: 'SPEC-4' }).click();
  await expect(page.getByRole('region', { name: 'Your review' })).toBeVisible();
});

test('My work says when nothing needs the person', async ({ page }) => {
  await inAcme(page, 'viewer', { specs: [] });

  await page.goto('/app/acme');

  await expect(page.getByText('Nothing is waiting for your review.')).toBeVisible();
  await expect(page.getByText('You don’t own a spec that’s still to be built.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Write one' })).toHaveCount(0);
  await expect(page.getByText('No criterion of your specs is failing.')).toBeVisible();
});
