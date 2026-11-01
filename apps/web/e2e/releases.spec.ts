import { readFile } from 'node:fs/promises';
import { expect, type Page, test } from '@playwright/test';
import { type HeldProof, standInEvidence } from './evidence';
import { type HeldRelease, standInReleases } from './releases';
import { question, request, standInRequests } from './requests';
import { criterion, type HeldSpec, spec, standInSpecs } from './specs';
import { signedIn, standIn } from './supabase';
import { acme, ada, ben, member, type Role, standInTeam, team } from './workspaces';

// A request's delivery: what stands between it and a release, a person approving one once every
// criterion is proven, and each release's document (decision record 62).

const booking = request(acme, 2, 'A booking app', {
  body: 'Members book classes from their phones.',
});
const drafted = spec(acme, 3, 'Book a class', {
  status: 'implemented',
  request: { id: booking.id, number: booking.number, title: booking.title },
});
const criteria = [
  criterion(drafted, 1, 'A member books a class'),
  criterion(drafted, 2, 'A full class refuses a booking'),
];
const proofOf = (number: 1 | 2, passed: number): HeldProof => ({
  criterion: criteria[number - 1]?.id ?? '',
  spec: { id: drafted.id, number: drafted.number, title: drafted.title },
  number,
  text: criteria[number - 1]?.text ?? '',
  passed,
  failed: 0,
  skipped: 0,
  suspectSince: null,
});
const snapshot = [
  {
    number: 3,
    title: 'Book a class',
    status: 'implemented',
    criteria: [
      { number: 1, text: 'A member books a class', tests: 2 },
      { number: 2, text: 'A full class refuses a booking', tests: 1 },
    ],
    tasks: [
      {
        number: 7,
        title: 'Build the booking API',
        role: 'build',
        status: 'done',
        pull_request: 'https://github.com/acme-co/booking/pull/12',
      },
    ],
  },
];

/** Signed in as Ada, with the given role in Acme, where Ben is an owner. */
async function inAcme(
  page: Page,
  role: Role,
  {
    proofs = [proofOf(1, 2), proofOf(2, 1)],
    specs = [drafted],
    releases = [],
  }: { proofs?: HeldProof[]; specs?: HeldSpec[]; releases?: HeldRelease[] } = {},
) {
  await standIn(page);
  await standInTeam(
    page,
    team({ workspaces: [acme], members: [member(acme, ada, role), member(acme, ben, 'owner')] }),
  );
  await standInSpecs(page, { specs, criteria });
  await standInEvidence(page, acme, { proofs });
  await standInRequests(page, {
    requests: [booking],
    questions: [
      question(booking, 1, 'Do members pay when they book?', {
        answer: 'Yes, by card.',
        answeredBy: ada.id,
        answeredAt: new Date().toISOString(),
      }),
    ],
    specs,
  });
  const calls = await standInReleases(page, { releases, snapshot });
  await signedIn(page);
  return calls;
}

test('a request waits for its criteria to be proven, saying which ones', async ({ page }) => {
  await inAcme(page, 'member', { proofs: [proofOf(1, 2), proofOf(2, 0)] });

  await page.goto('/app/acme/REQ-2');
  const delivery = page.getByRole('region', { name: 'Delivery' });
  await expect(delivery).toContainText('Release 1 can be approved once these are done:');
  await expect(delivery.getByRole('listitem')).toHaveText([
    'SPEC-3 has 1 of 2 criteria not proven yet: AC-2.',
  ]);
  await expect(delivery.getByRole('button', { name: 'Approve release 1' })).toBeDisabled();
});

test('a member approves the release once everything is proven, and downloads its document', async ({
  page,
}) => {
  const calls = await inAcme(page, 'member');

  await page.goto('/app/acme/REQ-2');
  const delivery = page.getByRole('region', { name: 'Delivery' });
  await expect(delivery).toContainText(
    'Every spec drafted from it is approved and every criterion is proven by the tests.',
  );
  await delivery.getByRole('button', { name: 'Approve release 1' }).click();
  const dialog = page.getByRole('dialog', { name: 'Approve release 1 of REQ-2' });
  await dialog.getByRole('textbox', { name: 'Note' }).fill('For the front desk.');
  await dialog.getByRole('button', { name: 'Approve release' }).click();
  await expect(dialog).toBeHidden();
  expect(calls.rpc).toEqual([
    { name: 'approve_release', args: { request: booking.id, note: 'For the front desk.' } },
  ]);

  await expect(delivery).toContainText('Release 1Approved by Ada Lovelace');
  await expect(delivery.getByRole('button', { name: 'Approve release 2' })).toBeVisible();
  const download = page.waitForEvent('download');
  await delivery.getByRole('button', { name: 'Download' }).click();
  const file = await download;
  expect(file.suggestedFilename()).toBe('REQ-2-release-1.md');
  const text = await readFile(await file.path(), 'utf8');
  expect(text.split('\n').slice(0, 5)).toEqual([
    '# REQ-2 A booking app: release 1',
    '',
    expect.stringMatching(/^Approved by Ada Lovelace on \w+ \d{1,2}, \d{4} \(UTC\)\.$/),
    '',
    '> For the front desk.',
  ]);
  expect(text).toContain('- **Do members pay when they book?**\n  Yes, by card.');
  expect(text).toContain('| AC-1 A member books a class | 2 tests |');
  expect(text).toContain(
    '- TASK-7 Build the booking API (Build; Done, https://github.com/acme-co/booking/pull/12)',
  );
});

test('a viewer reads the releases but approves none', async ({ page }) => {
  await inAcme(page, 'viewer', {
    releases: [
      {
        id: 'b4000000-0000-4000-8000-000000000001',
        request: booking.id,
        number: 1,
        note: null,
        approvedBy: ben.id,
        approvedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        snapshot,
      },
    ],
  });

  await page.goto('/app/acme/REQ-2');
  const delivery = page.getByRole('region', { name: 'Delivery' });
  await expect(delivery).toContainText('Release 1Approved by Ben Ortiz');
  await expect(delivery.getByRole('button', { name: /Approve release/ })).toHaveCount(0);
  await expect(delivery.getByRole('button', { name: 'Download' })).toBeVisible();
});
