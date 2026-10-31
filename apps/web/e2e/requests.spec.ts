import { expect, type Page, test } from '@playwright/test';
import {
  type HeldQuestion,
  type HeldRequest,
  question,
  request,
  standInRequests,
} from './requests';
import { criterion, type HeldSpec, spec, standInSpecs } from './specs';
import { signedIn, standIn } from './supabase';
import { acme, ada, ben, member, type Role, standInTeam, team } from './workspaces';

// Requests in people's own words, the questions agents ask about them, and the specs drafted
// from them (decision record 60).

const booking = request(acme, 2, 'A booking app for our gym', {
  body: 'Members book and pay for classes from their phones.',
});
const asked = [
  question(booking, 1, 'Do members pay when they book, or at the class?'),
  question(booking, 2, 'Which card reader do you use?', {
    answer: 'A Square Terminal.',
    answeredBy: ada.id,
    answeredAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  }),
];
const drafted = spec(acme, 3, 'Book a class', {
  status: 'draft',
  request: { id: booking.id, number: booking.number, title: booking.title },
});

/** Signed in as Ada, with the given role in Acme, where Ben is an owner. */
async function inAcme(
  page: Page,
  role: Role,
  {
    requests = [booking],
    questions = asked,
    specs = [drafted],
  }: { requests?: HeldRequest[]; questions?: HeldQuestion[]; specs?: HeldSpec[] } = {},
) {
  await standIn(page);
  await standInTeam(
    page,
    team({ workspaces: [acme], members: [member(acme, ada, role), member(acme, ben, 'owner')] }),
  );
  await standInSpecs(page, { specs, criteria: [criterion(drafted, 1, 'A member books a class')] });
  const calls = await standInRequests(page, { requests, questions, specs });
  await signedIn(page);
  return calls;
}

test('a member writes the first request, which opens at its ID', async ({ page }) => {
  const calls = await inAcme(page, 'member', { requests: [], questions: [], specs: [] });

  await page.goto('/app/acme/requests');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Requests');
  const empty = page.getByRole('region', { name: 'No requests yet' });
  await expect(empty).toContainText('A request says what you want built, in your own words.');
  await empty.getByRole('button', { name: 'Write the first request' }).click();

  const dialog = page.getByRole('dialog', { name: 'New request' });
  await dialog.getByRole('button', { name: 'Send request' }).click();
  await expect(dialog.getByText('Say what you want built.')).toBeVisible();
  await dialog.getByRole('textbox', { name: 'What do you want built?' }).fill('A booking app');
  await dialog.getByRole('textbox', { name: 'Details' }).fill('For our gym’s members.');
  await dialog.getByRole('button', { name: 'Send request' }).click();

  await expect(page).toHaveURL(/\/app\/acme\/REQ-1$/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('A booking app');
  await expect(page.getByText('No questions yet.')).toBeVisible();
  await expect(page.getByText('No specs drafted from it yet.')).toBeVisible();
  expect(calls.rpc).toEqual([
    {
      name: 'create_request',
      args: { workspace: acme.id, title: 'A booking app', body: 'For our gym’s members.' },
    },
  ]);
});

test('the Requests page lists each request with its open questions and specs', async ({ page }) => {
  await inAcme(page, 'viewer');

  await page.goto('/app/acme/requests');
  await expect(page.getByText('1 request', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'New request' })).toHaveCount(0);
  await expect(page.getByRole('row').nth(1)).toContainText(
    'REQ-2A booking app for our gymOpen1 to answer1Ada Lovelace',
  );

  await page.getByRole('link', { name: 'A booking app for our gym' }).click();
  await expect(page).toHaveURL(/\/app\/acme\/REQ-2$/);
  const sidebar = page.getByRole('navigation', { name: 'Workspace' });
  await expect(sidebar.getByRole('link', { name: 'Requests' })).toHaveAttribute(
    'aria-current',
    'page',
  );
  await expect(sidebar.getByRole('link', { name: 'Specs' })).not.toHaveAttribute('aria-current');
});

test('the writer answers an agent’s question, and reaches the spec drafted from it', async ({
  page,
}) => {
  const calls = await inAcme(page, 'member');

  await page.goto('/app/acme/REQ-2');
  await expect(page.getByRole('textbox', { name: 'Title' })).toHaveValue(
    'A booking app for our gym',
  );
  const questions = page.getByRole('region', { name: 'Questions' });
  const [first, second] = [
    questions.getByRole('listitem').nth(0),
    questions.getByRole('listitem').nth(1),
  ];
  await expect(first).toContainText('Do members pay when they book, or at the class?');
  await expect(first).toContainText('Ada Lovelace’s agent, Claude Code · 1 hour ago');
  await expect(second).toContainText('A Square Terminal.');
  await expect(second).toContainText('Ada Lovelace · 30 minutes ago');

  await first.getByRole('button', { name: 'Answer' }).click();
  await expect(first.getByText('Write an answer.')).toBeVisible();
  await first.getByRole('textbox', { name: 'Your answer' }).fill('When they book.');
  await first.getByRole('button', { name: 'Answer' }).click();
  await expect(first).toContainText('When they book.');
  await expect(first.getByRole('textbox', { name: 'Your answer' })).toHaveCount(0);
  expect(calls.rpc).toEqual([
    { name: 'answer_question', args: { question: asked[0]?.id, answer: 'When they book.' } },
  ]);

  await page
    .getByRole('region', { name: 'Specs' })
    .getByRole('link', { name: 'Book a class' })
    .click();
  await expect(page).toHaveURL(/\/app\/acme\/SPEC-3$/);
  const details = page.getByRole('complementary', { name: 'Details' });
  await details.getByRole('link', { name: 'REQ-2 A booking app for our gym' }).click();
  await expect(page).toHaveURL(/\/app\/acme\/REQ-2$/);
});

test('a planned request takes no more answers', async ({ page }) => {
  const calls = await inAcme(page, 'member');

  await page.goto('/app/acme/REQ-2');
  const questions = page.getByRole('region', { name: 'Questions' });
  await expect(questions.getByRole('textbox', { name: 'Your answer' })).toBeVisible();
  await page.getByRole('button', { name: 'Status' }).click();
  await page.getByRole('option', { name: /^Planned/ }).click();

  await expect(questions.getByText('Waiting for an answer')).toBeVisible();
  await expect(questions.getByRole('textbox', { name: 'Your answer' })).toHaveCount(0);
  await expect(questions.getByRole('button', { name: 'Change answer' })).toHaveCount(0);
  expect(calls.patches).toEqual([{ status: 'planned' }]);
});

test('a viewer reads a request and its questions but changes nothing', async ({ page }) => {
  await inAcme(page, 'viewer');

  await page.goto('/app/acme/REQ-2');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('A booking app for our gym');
  await expect(page.getByRole('textbox', { name: 'Title' })).toHaveCount(0);
  const questions = page.getByRole('region', { name: 'Questions' });
  await expect(questions.getByText('Waiting for an answer')).toBeVisible();
  await expect(questions.getByRole('button')).toHaveCount(0);
  await expect(page.getByRole('complementary', { name: 'Details' })).toContainText('StatusOpen');
});

test('My work puts the questions on the person’s open requests first', async ({ page }) => {
  await inAcme(page, 'member', { specs: [] });

  await page.goto('/app/acme');
  await expect(page.getByText('1 to answer', { exact: true })).toBeVisible();
  const waiting = page.getByRole('region', { name: 'Questions for you' });
  await expect(waiting.getByRole('row')).toHaveCount(2);
  await expect(waiting.getByRole('row').nth(1)).toContainText(
    'REQ-2Do members pay when they book, or at the class?A booking app for our gymAda Lovelace’s agent, Claude Code1 hour ago',
  );

  await waiting.getByRole('link', { name: 'REQ-2' }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('A booking app for our gym');
});

test('a request’s ID that hasn’t been written says so', async ({ page }) => {
  await inAcme(page, 'member');

  await page.goto('/app/acme/REQ-9');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('No request here');
  await expect(page.getByText('REQ-9 hasn’t been written in this workspace.')).toBeVisible();
});
