import { expect, test } from '@playwright/test';
import { standInSpecs } from './specs';
import { learner, signedIn, standIn, supabase } from './supabase';
import { acme, ada, ben, link, member, standInTeam, team } from './workspaces';

// The app, apps/app, which the site's Worker serves under /app/ (decision record 47), and its
// workspaces and members (decision record 48).

test('signed out, the app offers sign-in that comes back to it, and loads nothing from Supabase', async ({
  page,
}) => {
  const origins = new Set<string>();
  page.on('request', (request) => origins.add(new URL(request.url()).origin));

  await page.goto('/app/', { waitUntil: 'networkidle' });

  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Sign in to Sulba');
  await expect(page.getByRole('link', { name: 'Sign in' })).toHaveAttribute(
    'href',
    '/sign-in/?next=%2Fapp%2F',
  );
  expect(origins.has(supabase)).toBe(false);
});

test('an address under /app/ is answered with the app, which says when it has no such page', async ({
  page,
}) => {
  const response = await page.goto('/app/nothing/here/at/all/');

  expect(response?.status()).toBe(200);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Page not found');
  await page.getByRole('link', { name: 'Go to Sulba' }).click();
  await expect(page).toHaveURL(/\/app\/$/);
});

test('someone in no workspace creates one, whose address follows its name, and becomes its owner', async ({
  page,
}) => {
  await standIn(page);
  const calls = await standInTeam(page, team());
  await standInSpecs(page);
  await signedIn(page);

  await page.goto('/app/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Create a workspace');
  await page.getByLabel('Workspace name').fill('Acme Robotics');
  await expect(page.getByLabel('Address')).toHaveValue('acme-robotics');
  await page.getByRole('button', { name: 'Create workspace' }).click();

  await expect(page).toHaveURL(/\/app\/acme-robotics$/);
  await expect(page).toHaveTitle('My work · Acme Robotics · Sulba');
  await page.getByRole('link', { name: 'Members' }).click();
  await expect(page.getByRole('row', { name: /Ada Lovelace \(you\)/ })).toContainText('Owner');
  expect(calls.rpc).toEqual([
    { name: 'create_workspace', args: { name: 'Acme Robotics', slug: 'acme-robotics' } },
  ]);
});

test('a workspace’s address is checked as it’s typed, and a taken one is said on its field', async ({
  page,
}) => {
  await standIn(page);
  await standInTeam(page, team({ workspaces: [acme], members: [member(acme, ben, 'owner')] }));
  await signedIn(page);

  await page.goto('/app/new');
  await page.getByLabel('Workspace name').fill('Acme');
  await page.getByLabel('Address').fill('a--b');
  await expect(page.getByText('A hyphen goes between two letters or digits.')).toBeVisible();

  await page.getByLabel('Address').fill('acme');
  await page.getByRole('button', { name: 'Create workspace' }).click();
  await expect(page.getByLabel('Address')).toHaveAttribute('aria-invalid', 'true');
  await expect(page.getByText('That address is taken.')).toBeVisible();
  await expect(page).toHaveURL(/\/app\/new$/);
});

test('the front door lists the person’s workspaces, then goes back to the one opened last', async ({
  page,
}) => {
  const other = { id: 'b0000000-0000-4000-8000-000000000002', name: 'Bolt', slug: 'bolt' };
  await standIn(page);
  await standInTeam(
    page,
    team({
      workspaces: [acme, other],
      members: [member(acme, ada, 'owner'), member(other, ada, 'viewer')],
    }),
  );
  await standInSpecs(page);
  await signedIn(page);

  await page.goto('/app/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Your workspaces');
  await expect(page.getByText(`Signed in as ${learner.email}`)).toBeVisible();
  await expect(page.getByRole('link', { name: /Bolt/ })).toContainText(
    'sulba.dev/app/bolt · Viewer',
  );

  await page.getByRole('link', { name: /Bolt/ }).click();
  await expect(page).toHaveURL(/\/app\/bolt$/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('My work');

  // The browser remembers the workspace it opened last, and the front door goes back to it.
  await page.goto('/app/');
  await expect(page).toHaveURL(/\/app\/bolt$/);
});

test('signing out from the workspace menu ends the session', async ({ page }) => {
  const calls = await standIn(page);
  await standInTeam(page, team({ workspaces: [acme], members: [member(acme, ada, 'owner')] }));
  await signedIn(page);

  await page.goto('/app/acme/members');
  await page.getByRole('button', { name: 'Acme, switch workspace' }).click();
  await page.getByRole('menuitem', { name: 'Sign out' }).click();

  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Sign in to Sulba');
  expect(calls.logouts).toBe(1);
  expect(await page.evaluate(() => localStorage.getItem('sulba:session'))).toBeNull();
});

test('an admin makes an invitation link, shown once to copy, and can revoke it', async ({
  page,
}) => {
  await standIn(page);
  const calls = await standInTeam(
    page,
    team({ workspaces: [acme], members: [member(acme, ada, 'admin'), member(acme, ben, 'owner')] }),
  );
  await signedIn(page);

  await page.goto('/app/acme/members');
  await expect(page.getByText('No open links. A link lasts 7 days.')).toBeVisible();
  await page.getByRole('button', { name: 'Invite people' }).click();
  const dialog = page.getByRole('dialog', { name: 'Invite people' });
  await dialog.getByRole('button', { name: /They join as/ }).click();
  await page.getByRole('option', { name: /^Viewer/ }).click();
  await dialog.getByRole('button', { name: 'Create link' }).click();

  const field = dialog.getByRole('textbox', { name: 'Invitation link' });
  await expect(field).toHaveValue(/\/app\/join\/[0-9a-f]{64}$/);
  await expect(dialog).toContainText('join Acme as a viewer for 7 days');
  expect(calls.rpc).toEqual([
    { name: 'create_invitation', args: { workspace: acme.id, role: 'viewer' } },
  ]);
  await dialog.getByRole('button', { name: 'Done' }).click();

  const links = page.getByRole('region', { name: 'Invitation links' });
  await expect(links.getByRole('row', { name: /Viewer Ada Lovelace/ })).toBeVisible();
  await links.getByRole('button', { name: 'Revoke' }).click();
  await expect(page.getByText('No open links. A link lasts 7 days.')).toBeVisible();
});

test('signed out, an invitation link says what it offers and signs in to accept it', async ({
  page,
}) => {
  await page.route(`${supabase}/**`, (route) => route.abort());
  await standInTeam(page, team({ workspaces: [acme], invitations: [link(acme, 'a'.repeat(64))] }));

  await page.goto(`/app/join/${'a'.repeat(64)}`);

  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Join Acme');
  await expect(page.getByText('You’re invited to join Acme as a member.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Sign in' })).toHaveAttribute(
    'href',
    `/sign-in/?next=${encodeURIComponent(`/app/join/${'a'.repeat(64)}`)}`,
  );
});

test('signed in, accepting an invitation joins the workspace and opens it', async ({ page }) => {
  await standIn(page);
  const calls = await standInTeam(
    page,
    team({
      workspaces: [acme],
      members: [member(acme, ben, 'owner')],
      invitations: [link(acme, 'b'.repeat(64))],
    }),
  );
  await standInSpecs(page);
  await signedIn(page);

  await page.goto(`/app/join/${'b'.repeat(64)}`);
  await expect(
    page.getByText(`You’ll join as a member, signed in as ${learner.email}.`),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Join Acme' }).click();

  await expect(page).toHaveURL(/\/app\/acme$/);
  await page.getByRole('link', { name: 'Members' }).click();
  await expect(page.getByRole('row', { name: /Ada Lovelace \(you\)/ })).toContainText('Member');
  expect(calls.rpc.map(({ name }) => name)).toEqual(['invitation', 'accept_invitation']);
});

test('an expired or revoked invitation link says so', async ({ page }) => {
  await page.route(`${supabase}/**`, (route) => route.abort());
  await standInTeam(page, team({ workspaces: [acme] }));

  await page.goto(`/app/join/${'c'.repeat(64)}`);

  await expect(page.getByRole('heading', { level: 1 })).toHaveText('This invitation has expired');
});

test('an owner changes a member’s role, and a viewer sees roles without changing them', async ({
  page,
}) => {
  await standIn(page);
  const held = team({
    workspaces: [acme],
    members: [member(acme, ada, 'owner'), member(acme, ben, 'member')],
  });
  const calls = await standInTeam(page, held);
  await signedIn(page);

  await page.goto('/app/acme/members');
  await page.getByRole('button', { name: /Ben Ortiz’s role/ }).click();
  await page.getByRole('option', { name: /^Admin/ }).click();
  await expect(page.getByRole('button', { name: /Ben Ortiz’s role/ })).toContainText('Admin');
  expect(calls.rpc).toEqual([
    { name: 'set_member_role', args: { workspace: acme.id, person: ben.id, role: 'admin' } },
  ]);

  // As a viewer, the same page shows each role and offers only to leave.
  const self = held.members.find((each) => each.person === learner.id);
  if (self) self.role = 'viewer';
  await page.reload();
  await expect(page.getByRole('row', { name: /Ben Ortiz/ })).toContainText('Admin');
  await expect(page.getByRole('button', { name: /’s role/ })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Invite people' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Remove' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Leave' })).toBeVisible();
});

test('the only owner can’t leave, and is told why', async ({ page }) => {
  await standIn(page);
  await standInTeam(
    page,
    team({
      workspaces: [acme],
      members: [member(acme, ada, 'owner'), member(acme, ben, 'member')],
    }),
  );
  await signedIn(page);

  await page.goto('/app/acme/settings');
  await page.getByRole('button', { name: 'Leave workspace' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Leave' }).click();

  await expect(page.getByRole('alert')).toHaveText(
    'A workspace needs an owner: make someone else an owner first.',
  );
  await expect(page).toHaveURL(/\/app\/acme\/settings$/);
});

test('an admin renames the workspace, and its address stays', async ({ page }) => {
  await standIn(page);
  await standInTeam(page, team({ workspaces: [acme], members: [member(acme, ada, 'admin')] }));
  await signedIn(page);

  await page.goto('/app/acme/settings');
  await expect(page.getByLabel('Address')).toHaveValue('sulba.dev/app/acme');
  await expect(page.getByRole('button', { name: 'Delete workspace' })).toHaveCount(0);
  await page.getByLabel('Name', { exact: true }).fill('Acme Robotics');
  await page.getByRole('button', { name: 'Save' }).click();

  await expect(page.getByRole('button', { name: 'Saved' })).toBeDisabled();
  await expect(page.getByRole('button', { name: /switch workspace/ })).toHaveAccessibleName(
    'Acme Robotics, switch workspace',
  );
});

test('an owner deletes the workspace only after typing its name', async ({ page }) => {
  await standIn(page);
  const calls = await standInTeam(
    page,
    team({ workspaces: [acme], members: [member(acme, ada, 'owner')] }),
  );
  await signedIn(page);

  await page.goto('/app/acme/settings');
  await page.getByRole('button', { name: 'Delete workspace' }).click();
  const dialog = page.getByRole('dialog', { name: 'Delete Acme?' });
  const remove = dialog.getByRole('button', { name: 'Delete workspace' });
  await expect(remove).toBeDisabled();
  await dialog.getByLabel('Workspace name').fill('Acme');
  await remove.click();

  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Create a workspace');
  expect(calls.rpc).toEqual([{ name: 'delete_workspace', args: { workspace: acme.id } }]);
});

test('an address with no workspace of the person’s says so', async ({ page }) => {
  await standIn(page);
  await standInTeam(page, team({ workspaces: [acme], members: [member(acme, ben, 'owner')] }));
  await signedIn(page);

  await page.goto('/app/acme/members');

  await expect(page.getByRole('heading', { level: 1 })).toHaveText('No workspace here');
});
