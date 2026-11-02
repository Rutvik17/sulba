import { expect, type Page, test } from '@playwright/test';
import { question, request, standInRequests } from './requests';
import { type HeldRun, standInRuns } from './runs';
import { standInSpecs } from './specs';
import { signedIn, standIn } from './supabase';
import { acme, ada, ben, member, type Role, standInTeam, team } from './workspaces';

// Sulba's own agents on a request: a member starts Sulba Intake within the workspace's monthly
// allowance, its run shows what it may spend and then what it did and cost, and its questions
// come back to the request (decision records 63 and 64).

const booking = request(acme, 2, 'A booking app', {
  body: 'Members book classes from their phones.',
});

/** Signed in as Ada, with the given role in Acme, where Ben is an owner. */
async function inAcme(
  page: Page,
  role: Role,
  options: { runs?: HeldRun[]; limitCents?: number; refusal?: string } = {},
) {
  await standIn(page);
  await standInTeam(
    page,
    team({ workspaces: [acme], members: [member(acme, ada, role), member(acme, ben, 'owner')] }),
  );
  await standInSpecs(page);
  const requests = await standInRequests(page, { requests: [booking] });
  const runs = await standInRuns(page, options);
  await signedIn(page);
  return { requests, runs };
}

test('a workspace without an allowance can’t start Sulba’s agents', async ({ page }) => {
  await inAcme(page, 'member', { limitCents: 0 });

  await page.goto('/app/acme/REQ-2');
  const agents = page.getByRole('region', { name: 'Sulba’s agents' });
  await expect(agents).toContainText(
    'Reads the request and asks its writer what it needs to know before specs are drafted.',
  );
  await expect(agents).toContainText('This workspace has no allowance for Sulba’s agents yet.');
  await expect(agents.getByRole('button', { name: 'Ask Sulba Intake' })).toBeDisabled();
});

test('a member asks Sulba Intake, and its questions come back to the request', async ({ page }) => {
  const { requests, runs } = await inAcme(page, 'member');

  await page.goto('/app/acme/REQ-2');
  const agents = page.getByRole('region', { name: 'Sulba’s agents' });
  await expect(agents).toContainText('$0.00 of this month’s $2.50 spent.');
  await agents.getByRole('button', { name: 'Ask Sulba Intake' }).click();

  const list = agents.getByRole('list', { name: 'Runs' });
  await expect(list.getByRole('listitem')).toHaveText([
    /^Sulba IntakeWorking on it\.Started .+ · up to \$1\.00$/,
  ]);
  expect(runs.started).toEqual([
    {
      body: { request: booking.id, role: 'intake' },
      authorization: expect.stringMatching(/^Bearer \S+$/),
      run: expect.any(String),
    },
  ]);
  await expect(agents.getByRole('button', { name: 'Working…' })).toBeDisabled();
  await expect(agents).toContainText(
    '$0.00 of this month’s $2.50 spent, and $1.00 set aside while an agent works.',
  );

  // Intake finishes with two questions, which the Worker asks for Ada.
  const now = new Date().toISOString();
  ['Do members pay when they book?', 'Which classes can be booked?'].forEach((text, index) => {
    requests.ask(
      question(booking, index + 1, text, {
        askedBy: ada.id,
        askedByAgent: 'Sulba Intake',
        askedAt: now,
      }),
    );
  });
  runs.finish(String(runs.started[0]?.run), { costCents: 37, note: 'Asked 2 questions.' });

  await expect(list.getByRole('listitem')).toHaveText(
    [/^Sulba IntakeAsked 2 questions\.Done · .+ · \$0\.37$/],
    { timeout: 15_000 },
  );
  await expect(agents).toContainText('$0.37 of this month’s $2.50 spent.');
  const questions = page.getByRole('region', { name: 'Questions' });
  await expect(questions).toContainText('Do members pay when they book?');
  await expect(questions).toContainText('Ada Lovelace’s agent, Sulba Intake');
  await expect(agents.getByRole('button', { name: 'Ask Sulba Intake' })).toBeEnabled();
});

test('a refused run says why', async ({ page }) => {
  await inAcme(page, 'member', {
    refusal: 'This workspace has used its agent allowance for this month',
  });

  await page.goto('/app/acme/REQ-2');
  const agents = page.getByRole('region', { name: 'Sulba’s agents' });
  await agents.getByRole('button', { name: 'Ask Sulba Intake' }).click();
  await expect(agents.getByRole('alert')).toHaveText(
    'This workspace has used its agent allowance for this month.',
  );
});

test('a viewer sees the runs and what they cost, but starts none', async ({ page }) => {
  await inAcme(page, 'viewer', {
    runs: [
      {
        id: 'c3000000-0000-4000-8000-000000000001',
        request: booking.id,
        status: 'stopped',
        budgetCents: 100,
        costCents: 100,
        note: 'Reached its budget.',
        startedBy: ben.id,
        startedAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
        endedAt: new Date().toISOString(),
      },
    ],
  });

  await page.goto('/app/acme/REQ-2');
  const agents = page.getByRole('region', { name: 'Sulba’s agents' });
  await expect(agents.getByRole('listitem')).toHaveText([
    /^Sulba IntakeReached its budget\.Stopped · 1 hour ago · \$1\.00$/,
  ]);
  await expect(agents.getByRole('button')).toHaveCount(0);
});
