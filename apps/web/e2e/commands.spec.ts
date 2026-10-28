import { expect, type Page, test } from '@playwright/test';
import { standInEvidence } from './evidence';
import { criterion, spec, standInSpecs } from './specs';
import { signedIn, standIn } from './supabase';
import { acme, ada, ben, member, type Role, standInTeam, team } from './workspaces';

// The command menu and the keys that run the same commands (decision record 53).

// Phones have no keyboard to press shortcuts on.
test.skip(({ isMobile }) => isMobile, 'Shortcuts need a keyboard');

const bolt = { id: 'b0000000-0000-4000-8000-000000000002', name: 'Bolt', slug: 'bolt' };
const retry = spec(acme, 3, 'Retry failed payments', { status: 'draft' });
const refunds = spec(acme, 4, 'Refund a payment', { status: 'draft' });

/** Signed in as Ada, with the given role in Acme and a viewer in Bolt. */
async function inAcme(page: Page, role: Role = 'member') {
  await standIn(page);
  await standInTeam(
    page,
    team({
      workspaces: [acme, bolt],
      members: [member(acme, ada, role), member(acme, ben, 'owner'), member(bolt, ada, 'viewer')],
    }),
  );
  const calls = await standInSpecs(page, {
    specs: [retry, refunds],
    criteria: [criterion(retry, 1, 'A failed payment is retried once')],
  });
  await standInEvidence(page, acme);
  await signedIn(page);
  return calls;
}

/** The key held with K to open the menu: Cmd where the browser says it's on a Mac. */
async function menuKey(page: Page): Promise<string> {
  const mac = await page.evaluate(() => /Mac|iPhone|iPad|iPod/.test(navigator.userAgent));
  return mac ? 'Meta+k' : 'Control+k';
}

test('Cmd or Ctrl K opens the menu, which finds a command and runs it on Enter', async ({
  page,
}) => {
  await inAcme(page);
  await page.goto('/app/acme');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('My work');

  await page.keyboard.press(await menuKey(page));
  const menu = page.getByRole('dialog', { name: 'Commands' });
  await expect(menu.getByRole('textbox', { name: 'Commands' })).toBeFocused();
  await expect(menu.getByRole('menuitem', { name: 'Go to Members' })).toHaveAccessibleDescription(
    'G then M',
  );
  await page.keyboard.type('members');
  await page.keyboard.press('Enter');

  await expect(menu).toBeHidden();
  await expect(page).toHaveURL(/\/app\/acme\/members$/);
});

test('the sidebar’s button opens the menu, whose search finds a spec by its title', async ({
  page,
}) => {
  await inAcme(page);
  await page.goto('/app/acme');

  await page.getByRole('button', { name: 'Search or run a command' }).click();
  await page.getByRole('textbox', { name: 'Commands' }).fill('refund');
  await expect(page.getByRole('menuitem', { name: 'SPEC-4 Refund a payment' })).toBeVisible();
  await page.keyboard.press('Enter');

  await expect(page).toHaveURL(/\/app\/acme\/SPEC-4$/);
  await expect(page.getByRole('textbox', { name: 'Title' })).toHaveValue('Refund a payment');
});

test('G then a letter goes to a page, and keys typed in a field stay text', async ({ page }) => {
  await inAcme(page);
  await page.goto('/app/acme');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('My work');

  await page.keyboard.press('g');
  await page.keyboard.press('s');
  await expect(page).toHaveURL(/\/app\/acme\/specs$/);
  await page.keyboard.press('g');
  await page.keyboard.press('e');
  await expect(page).toHaveURL(/\/app\/acme\/evidence$/);

  // C opens a new spec; G then S typed into its title is the title.
  await page.keyboard.press('c');
  const dialog = page.getByRole('dialog', { name: 'New spec' });
  await expect(dialog).toBeVisible();
  await page.keyboard.type('gs');
  await expect(dialog.getByRole('textbox', { name: 'Title' })).toHaveValue('gs');
  await expect(page).toHaveURL(/\/app\/acme\/evidence$/);
});

test('on a spec, S lists its statuses and A its possible owners', async ({ page }) => {
  const calls = await inAcme(page);
  await page.goto('/app/acme/SPEC-3');
  await expect(page.getByRole('textbox', { name: 'Title' })).toHaveValue('Retry failed payments');

  await page.keyboard.press('s');
  const statuses = page.getByRole('dialog', { name: 'Change status' });
  await expect(statuses.getByRole('menuitem', { name: 'Draft' })).toContainText('Current');
  await statuses.getByRole('menuitem', { name: 'In review' }).click();
  await expect(statuses).toBeHidden();
  await expect(page.getByRole('button', { name: 'Status' })).toContainText('In review');

  await page.keyboard.press('a');
  await page.getByRole('textbox', { name: 'Change owner' }).fill('ben');
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: 'Owner' })).toContainText('Ben Ortiz');

  expect(calls.patches.map(({ body }) => body)).toEqual([
    { status: 'in_review' },
    { owner_id: ben.id },
  ]);
});

test('Backspace in a list’s empty search goes back to every command', async ({ page }) => {
  await inAcme(page);
  await page.goto('/app/acme/SPEC-3');
  await expect(page.getByRole('textbox', { name: 'Title' })).toHaveValue('Retry failed payments');

  await page.keyboard.press(await menuKey(page));
  await page.getByRole('menuitem', { name: 'Change status…' }).click();
  await expect(page.getByRole('dialog', { name: 'Change status' })).toBeVisible();
  await page.keyboard.press('Backspace');

  const menu = page.getByRole('dialog', { name: 'Commands' });
  await expect(menu.getByRole('menuitem', { name: 'Go to Specs' })).toBeVisible();
});

test('O then W switches workspace, and a viewer isn’t offered a new spec', async ({ page }) => {
  await inAcme(page);
  await page.goto('/app/acme');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('My work');

  await page.keyboard.press('o');
  await page.keyboard.press('w');
  const workspaces = page.getByRole('dialog', { name: 'Switch workspace' });
  await expect(workspaces.getByRole('menuitem')).toHaveText([/^AcmeCurrent/, /^Bolt/]);
  await workspaces.getByRole('menuitem', { name: 'Bolt' }).click();
  await expect(page).toHaveURL(/\/app\/bolt$/);

  await page.keyboard.press(await menuKey(page));
  await expect(page.getByRole('menuitem', { name: 'Go to Specs' })).toBeVisible();
  await expect(page.getByRole('menuitem', { name: 'Create a spec' })).toHaveCount(0);
  await page.keyboard.press('Escape');
  await page.keyboard.press('c');
  await expect(page.getByRole('dialog', { name: 'New spec' })).toHaveCount(0);
});

test('? lists the shortcuts, where single-key ones can be turned off for this browser', async ({
  page,
}) => {
  await inAcme(page);
  await page.goto('/app/acme/specs');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Specs');

  await page.keyboard.press('Shift+?');
  const shortcuts = page.getByRole('dialog', { name: 'Keyboard shortcuts' });
  await expect(
    shortcuts.getByRole('region', { name: 'Go to' }).getByRole('listitem'),
  ).toContainText(['Go to My work', 'Go to Specs', 'Go to Evidence']);
  const single = shortcuts.getByRole('switch', { name: 'Single-key shortcuts' });
  await expect(single).toBeChecked();
  await shortcuts.getByText('Single-key shortcuts').click();
  await expect(single).not.toBeChecked();
  await shortcuts.getByRole('button', { name: 'Close' }).click();

  await page.reload();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Specs');
  await page.keyboard.press('c');
  await page.keyboard.press('g');
  await page.keyboard.press('w');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page).toHaveURL(/\/app\/acme\/specs$/);

  // The menu's own keys hold Cmd or Ctrl, so they work either way.
  await page.keyboard.press(await menuKey(page));
  await expect(page.getByRole('dialog', { name: 'Commands' })).toBeVisible();
});
