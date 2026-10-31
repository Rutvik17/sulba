import { expect, type Page, test } from '@playwright/test';
import { criterion, type HeldSpec, spec, standInSpecs } from './specs';
import { signedIn, standIn } from './supabase';
import { type HeldTask, standInTasks, task } from './tasks';
import { acme, ada, ben, member, type Role, standInTeam, team } from './workspaces';

// Tasks written from approved specs, taken, blocked and handed in with a pull request, and marked
// done by people (decision record 61).

const retry = spec(acme, 3, 'Retry failed payments', { status: 'approved' });
const criteria = [
  criterion(retry, 1, 'A failed payment is retried once after 30 seconds'),
  criterion(retry, 2, 'A retry keeps the idempotency key'),
];
const handedIn = task(retry, 2, 'Build the retry job', {
  status: 'in_review',
  takenBy: ben.id,
  takenByAgent: 'Claude Code',
  note: 'Adds the job to the payments worker.',
  pullRequest: 'https://github.com/acme-co/payments/pull/12',
  criteria: [1, 2],
});

/** Signed in as Ada, with the given role in Acme, where Ben is an owner. */
async function inAcme(
  page: Page,
  role: Role,
  { specs = [retry], tasks = [] }: { specs?: HeldSpec[]; tasks?: HeldTask[] } = {},
) {
  await standIn(page);
  await standInTeam(
    page,
    team({ workspaces: [acme], members: [member(acme, ada, role), member(acme, ben, 'owner')] }),
  );
  await standInSpecs(page, { specs, criteria });
  const calls = await standInTasks(page, { tasks, specs, criteria });
  await signedIn(page);
  return calls;
}

test('a member writes a task from an approved spec, which opens at its ID', async ({ page }) => {
  const calls = await inAcme(page, 'member');

  await page.goto('/app/acme/SPEC-3');
  const tasks = page.getByRole('region', { name: 'Tasks' });
  await expect(tasks).toContainText('No tasks yet.');
  await tasks.getByRole('button', { name: 'Write a task' }).click();

  const dialog = page.getByRole('dialog', { name: 'New task for SPEC-3' });
  await expect(dialog).toContainText('It covers all 2 of SPEC-3’s criteria.');
  await dialog.getByRole('button', { name: 'Write task' }).click();
  await expect(dialog.getByText('Say what the task is.')).toBeVisible();
  await dialog.getByRole('textbox', { name: 'Title' }).fill('Test the retry job');
  await dialog.getByRole('button', { name: /Role/ }).click();
  await page.getByRole('option', { name: /^Test/ }).click();
  await dialog.getByRole('button', { name: 'Write task' }).click();

  await expect(page).toHaveURL(/\/app\/acme\/TASK-1$/);
  await expect(page.getByRole('textbox', { name: 'Title' })).toHaveValue('Test the retry job');
  await expect(page.getByRole('region', { name: 'Criteria it covers' })).toContainText(
    'SPEC-3/AC-1A failed payment is retried once after 30 secondsSPEC-3/AC-2A retry keeps the idempotency key',
  );
  expect(calls.rpc).toEqual([
    {
      name: 'create_task',
      args: {
        spec: retry.id,
        title: 'Test the retry job',
        role: 'test',
        body: '',
        criteria: [1, 2],
      },
    },
  ]);
});

test('a draft spec has no tasks to write', async ({ page }) => {
  await inAcme(page, 'member', { specs: [{ ...retry, status: 'draft' }] });

  await page.goto('/app/acme/SPEC-3');
  await expect(page.getByRole('region', { name: /^Acceptance criteria/ })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Tasks' })).toHaveCount(0);
});

test('the Tasks page lists each task with its role, spec, status and who has it', async ({
  page,
}) => {
  await inAcme(page, 'viewer', { tasks: [task(retry, 1, 'Test the retry job'), handedIn] });

  await page.goto('/app/acme/tasks');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Tasks');
  await expect(page.getByText('2 tasks', { exact: true })).toBeVisible();
  await expect(page.getByRole('row').nth(1)).toContainText(
    'TASK-2Build the retry jobBuildSPEC-3In reviewBen Ortiz’s agent, Claude Code',
  );
  await expect(page.getByRole('row').nth(2)).toContainText(
    'TASK-1Test the retry jobBuildSPEC-3OpenNo one',
  );

  await page.getByRole('link', { name: 'Build the retry job' }).click();
  await expect(page).toHaveURL(/\/app\/acme\/TASK-2$/);
  const sidebar = page.getByRole('navigation', { name: 'Workspace' });
  await expect(sidebar.getByRole('link', { name: 'Tasks' })).toHaveAttribute(
    'aria-current',
    'page',
  );
  await expect(page.getByRole('region', { name: 'Handed in' })).toContainText(
    'Handed in by Ben Ortiz’s agent, Claude CodeAdds the job to the payments worker.',
  );
  const details = page.getByRole('complementary', { name: 'Details' });
  await expect(details.getByRole('link', { name: 'acme-co/payments#12' })).toHaveAttribute(
    'href',
    'https://github.com/acme-co/payments/pull/12',
  );
  await expect(details.getByRole('button')).toHaveCount(0);
});

test('a member takes a task, blocks it saying why, resumes it and hands it in', async ({
  page,
}) => {
  const calls = await inAcme(page, 'member', { tasks: [task(retry, 1, 'Test the retry job')] });

  await page.goto('/app/acme/TASK-1');
  const details = page.getByRole('complementary', { name: 'Details' });
  await expect(details).toContainText('Taken byNo one');
  await details.getByRole('button', { name: 'Take it' }).click();
  await expect(details).toContainText('StatusIn progress');
  await expect(details).toContainText('Taken byAda Lovelace');

  await details.getByRole('button', { name: 'Block…' }).click();
  const block = page.getByRole('dialog', { name: 'Block TASK-1' });
  await block.getByRole('button', { name: 'Block' }).click();
  await expect(block.getByText('Say what blocks it.')).toBeVisible();
  await block.getByRole('textbox', { name: 'What blocks it?' }).fill('Which queue should it use?');
  await block.getByRole('button', { name: 'Block' }).click();
  await expect(block).toBeHidden();
  await expect(page.getByRole('region', { name: 'What blocks it' })).toContainText(
    'Blocked by Ada LovelaceWhich queue should it use?',
  );

  await details.getByRole('button', { name: 'Resume' }).click();
  await expect(details).toContainText('StatusIn progress');
  await details.getByRole('button', { name: 'Hand in…' }).click();
  const handIn = page.getByRole('dialog', { name: 'Hand in TASK-1' });
  await handIn.getByRole('textbox', { name: 'Pull request' }).fill('https://example.com/pull/12');
  await handIn.getByRole('button', { name: 'Hand in' }).click();
  await expect(
    handIn.getByText('A pull request’s address looks like https://github.com/owner/repo/pull/12.'),
  ).toBeVisible();
  await handIn
    .getByRole('textbox', { name: 'Pull request' })
    .fill('https://github.com/acme-co/payments/pull/13');
  await handIn.getByRole('button', { name: 'Hand in' }).click();
  await expect(handIn).toBeHidden();
  await expect(details).toContainText('StatusIn review');
  await expect(details.getByRole('link', { name: 'acme-co/payments#13' })).toBeVisible();

  expect(calls.rpc.map(({ args }) => args)).toEqual([
    { task: expect.any(String), status: 'in_progress' },
    { task: expect.any(String), status: 'blocked', note: 'Which queue should it use?' },
    { task: expect.any(String), status: 'in_progress' },
    {
      task: expect.any(String),
      status: 'in_review',
      pull_request: 'https://github.com/acme-co/payments/pull/13',
    },
  ]);
});

test('My work puts the tasks handed in on the person’s specs first, and they mark one done', async ({
  page,
}) => {
  const calls = await inAcme(page, 'member', { tasks: [handedIn] });

  await page.goto('/app/acme');
  await expect(page.getByText('1 task to check', { exact: false })).toBeVisible();
  const toCheck = page.getByRole('region', { name: 'Tasks to check' });
  await expect(toCheck.getByRole('row').nth(1)).toContainText(
    'TASK-2Build the retry jobSPEC-3 · acme-co/payments#12In reviewBen Ortiz’s agent, Claude Code',
  );

  await toCheck.getByRole('link', { name: 'TASK-2' }).click();
  const details = page.getByRole('complementary', { name: 'Details' });
  await details.getByRole('button', { name: 'Mark done' }).click();
  await expect(details).toContainText('StatusDone');
  await expect(details.getByRole('button', { name: 'Open again' })).toBeVisible();
  expect(calls.rpc).toEqual([{ name: 'update_task', args: { task: handedIn.id, status: 'done' } }]);
});

test('a task’s ID that hasn’t been written says so', async ({ page }) => {
  await inAcme(page, 'member');

  await page.goto('/app/acme/TASK-9');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('No task here');
  await expect(page.getByText('TASK-9 hasn’t been written in this workspace.')).toBeVisible();
});
