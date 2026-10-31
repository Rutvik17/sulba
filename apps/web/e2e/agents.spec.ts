import { expect, test } from '@playwright/test';
import { callback, standInConsent } from './agents';
import { signedIn, standIn } from './supabase';
import { acme, ada, member, standInTeam, team } from './workspaces';

// Coding agents connect through Supabase's OAuth server, which asks the person on the app's
// consent page, and the person disconnects them in Settings (decision record 51).

const asking = { id: 'f1e2d3c4-0000-4000-8000-000000000001', agent: 'Claude Code' };
const consent = `/app/oauth/consent?authorization_id=${asking.id}`;

test('a person allows an agent, which gets its code back', async ({ page }) => {
  await standIn(page);
  const answers = await standInConsent(page, asking);
  await signedIn(page);

  await page.goto(consent);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Connect Claude Code to Sulba');
  await expect(page).toHaveTitle(/^Connect an agent/);
  await expect(page.getByRole('main')).toContainText('Signed in as ada@example.com.');
  await expect(page.getByRole('region', { name: 'Request' })).toHaveText(
    'Claude CodeReturns you to 127.0.0.1:33418 on this computerOnly allow this if you just started connecting Claude Code on this computer.',
  );
  await expect(page.getByRole('region', { name: 'It will be able to' })).toContainText(
    'Ask you questions about a request',
  );
  const cannot = page.getByRole('region', { name: 'It won’t be able to' });
  await expect(cannot).toContainText('Write or change requests, or answer questions about them');
  await expect(cannot).toContainText('Approve a release');
  await page.getByRole('button', { name: 'Allow' }).click();

  await expect(page).toHaveURL(`${callback}?code=code-for-the-agent&state=agent-state`);
  expect(answers.actions).toEqual(['approve']);
});

test('an agent on a website says which, and the page says to allow it only from there', async ({
  page,
}) => {
  await standIn(page);
  await standInConsent(page, {
    ...asking,
    agent: 'Claude',
    returnTo: 'https://claude.ai/api/mcp/auth_callback',
  });
  await signedIn(page);

  await page.goto(consent);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Connect Claude to Sulba');
  await expect(page.getByRole('region', { name: 'Request' })).toContainText(
    'Returns you to claude.aiOnly allow this if you just started connecting Claude on claude.ai.',
  );
});

test('an agent that would send the answer anywhere but this computer or HTTPS is refused', async ({
  page,
}) => {
  await standIn(page);
  const answers = await standInConsent(page, {
    ...asking,
    returnTo: 'http://agent.example/callback',
  });
  await signedIn(page);

  await page.goto(consent);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('This agent can’t be connected');
  await expect(page.getByRole('main')).toContainText(
    'It asked to return you to http://agent.example/callback. Sulba only returns you to an app on this computer or to a website over HTTPS.',
  );
  await expect(page.getByRole('button', { name: 'Allow' })).toHaveCount(0);
  expect(answers.actions).toEqual([]);
});

test('a person cancels, and the agent is told it was denied', async ({ page }) => {
  await standIn(page);
  const answers = await standInConsent(page, asking);
  await signedIn(page);

  await page.goto(consent);
  await page.getByRole('button', { name: 'Cancel' }).click();

  await expect(page).toHaveURL(`${callback}?error=access_denied&state=agent-state`);
  expect(answers.actions).toEqual(['deny']);
});

test('an agent allowed before goes straight back', async ({ page }) => {
  await standIn(page);
  const answers = await standInConsent(page, { ...asking, allowedBefore: true });
  await signedIn(page);

  await page.goto(consent);

  await expect(page).toHaveURL(`${callback}?code=again`);
  expect(answers.actions).toEqual([]);
});

test('an expired request, or a link without one, says what to do', async ({ page }) => {
  await standIn(page);
  await standInConsent(page, { ...asking, expired: true });
  await signedIn(page);

  await page.goto(consent);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'This request can’t be answered',
  );
  await expect(page.getByRole('main')).toContainText(
    'This request has expired or was already answered. Connect again from your agent.',
  );

  await page.goto('/app/oauth/consent');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('This link is incomplete');
});

test('someone signed out signs in first and comes back to the request', async ({ page }) => {
  await standIn(page);
  await standInConsent(page, asking);

  await page.goto(consent);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Sign in to Sulba');
  await expect(page.getByRole('link', { name: 'Sign in' })).toHaveAttribute(
    'href',
    `/sign-in/?next=${encodeURIComponent(consent)}`,
  );
});

test('someone signed in to another account switches, and comes back to the request', async ({
  page,
}) => {
  const calls = await standIn(page);
  await standInConsent(page, asking);
  await signedIn(page);

  await page.goto(consent);
  await page.getByRole('button', { name: 'Use another account' }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Sign in to Sulba');
  await expect(page.getByRole('link', { name: 'Sign in' })).toHaveAttribute(
    'href',
    `/sign-in/?next=${encodeURIComponent(consent)}`,
  );
  expect(calls.logouts).toBe(1);
});

test('Settings gives each agent’s setup, and a person disconnects an agent', async ({ page }) => {
  const calls = await standIn(page, {
    agents: [
      {
        id: 'e0000000-0000-4000-8000-000000000005',
        name: 'Claude Code',
        grantedAt: '2026-10-21T09:00:00Z',
      },
      {
        id: 'e0000000-0000-4000-8000-000000000006',
        name: 'Cursor',
        grantedAt: '2026-10-27T09:00:00Z',
      },
    ],
  });
  await standInTeam(page, team({ workspaces: [acme], members: [member(acme, ada, 'member')] }));
  await signedIn(page);

  await page.goto('/app/acme/settings');
  const agents = page.getByRole('region', { name: 'Agents' });
  const origin = new URL(page.url()).origin;
  await expect(agents).toContainText(`claude mcp add --transport http sulba ${origin}/mcp`);
  await agents.getByRole('button', { name: 'Agent' }).click();
  await page.getByRole('option', { name: 'Codex' }).click();
  await expect(agents).toContainText(`codex mcp add sulba --url ${origin}/mcp`);
  await expect(agents).toContainText('codex mcp login sulba');

  const rows = agents.getByRole('row');
  await expect(rows).toHaveCount(3);
  await expect(rows.nth(1)).toContainText('Cursor');
  await expect(rows.nth(2)).toContainText('Claude Code');
  await expect(rows.nth(2).locator('time')).toHaveAttribute('datetime', '2026-10-21T09:00:00Z');
  await expect(rows.nth(2).locator('time')).toHaveText(/^Oct 21/);
  await rows.nth(2).getByRole('button', { name: 'Disconnect' }).click();
  const dialog = page.getByRole('dialog', { name: 'Disconnect Claude Code?' });
  await expect(dialog).toContainText('It stops acting for you at once, in every workspace.');
  await dialog.getByRole('button', { name: 'Disconnect' }).click();

  await expect(dialog).toBeHidden();
  await expect(rows).toHaveCount(2);
  expect(calls.disconnected).toEqual(['e0000000-0000-4000-8000-000000000005']);
});

test('Settings says when no agent is connected', async ({ page }) => {
  await standIn(page);
  await standInTeam(page, team({ workspaces: [acme], members: [member(acme, ada, 'viewer')] }));
  await signedIn(page);

  await page.goto('/app/acme/settings');

  await expect(page.getByRole('region', { name: 'Agents' })).toContainText(
    'No agents are connected yet.',
  );
});
