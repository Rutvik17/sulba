// Workspaces, the people in them and the links that invite people in (decision record 48).
// Postgres decides what each person may do; these calls ask it, and put its refusals in words.
import type { PostgrestError } from '@supabase/supabase-js';
import type { Client } from './client.ts';
import type { Database } from './database.ts';

export type Role = Database['public']['Enums']['workspace_role'];

/** Every role, from the one that may do least to the one that may do most. */
export const roles: readonly Role[] = ['viewer', 'member', 'admin', 'owner'];

export const roleNames: Record<Role, string> = {
  viewer: 'Viewer',
  member: 'Member',
  admin: 'Admin',
  owner: 'Owner',
};

export const roleAbilities: Record<Role, string> = {
  viewer: 'Sees everything in the workspace',
  member: 'Also makes changes',
  admin: 'Also invites people, changes their roles and renames the workspace',
  owner: 'Also makes owners and can delete the workspace',
};

/** The roles an invitation link can give. Admins and owners are made by changing a role. */
export const invitedRoles: readonly Role[] = ['viewer', 'member'];

/** Whether `role` may do what `minimum` may. */
export function holds(role: Role, minimum: Role): boolean {
  return roles.indexOf(role) >= roles.indexOf(minimum);
}

/** A workspace as the signed-in person sees it, with their role in it. */
export interface Workspace {
  readonly id: string;
  readonly name: string;
  /** Its address in the app: sulba.dev/app/<slug>. */
  readonly slug: string;
  readonly role: Role;
}

export interface Member {
  readonly personId: string;
  /** Empty when their sign-in gave no name. */
  readonly name: string;
  readonly email: string | null;
  readonly role: Role;
  readonly joinedAt: string;
}

export interface Invitation {
  readonly id: string;
  readonly role: Role;
  /** Who made the link, while they still have an account. */
  readonly madeBy: string | null;
  readonly createdAt: string;
  readonly expiresAt: string;
}

/** What an invitation link offers, before the person accepts it. */
export interface Offer {
  readonly workspaceName: string;
  readonly role: Role;
}

/** A refusal or failure, in words to show the person who asked. */
export class Refusal extends Error {
  override name = 'Refusal';
}

const reserved = new Set([
  'account',
  'admin',
  'api',
  'app',
  'assets',
  'docs',
  'help',
  'join',
  'login',
  'logout',
  'new',
  'settings',
  'sign-in',
  'sign-out',
  'static',
]);

/** The address a workspace's name suggests, which the person can change before creating it. */
export function slugOf(name: string): string {
  return name
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 32)
    .replace(/-+$/, '');
}

/** What's wrong with a workspace's name, or null. */
export function nameProblem(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed === '') return 'Give the workspace a name.';
  if (trimmed.length > 64) return 'A name has at most 64 characters.';
  return null;
}

/** What's wrong with a workspace's address, or null. Postgres checks it again. */
export function slugProblem(slug: string): string | null {
  if (slug.length < 3) return 'An address has at least 3 characters.';
  if (slug.length > 32) return 'An address has at most 32 characters.';
  if (!/^[a-z0-9-]+$/.test(slug)) return 'Use lowercase letters, digits and hyphens.';
  if (/^-|-$|--/.test(slug)) return 'A hyphen goes between two letters or digits.';
  if (reserved.has(slug)) return 'That address is taken.';
  return null;
}

/** The address of the page that accepts an invitation link. */
export function joinLink(origin: string, token: string): string {
  return `${origin}/app/join/${token}`;
}

/**
 * The words for a refusal. The functions in Postgres raise theirs for people to read, and each
 * becomes a sentence; anything else, such as a lost connection, gets a general one, and `taken`
 * names a duplicate.
 */
function refusal(error: PostgrestError, taken?: string): Refusal {
  if (error.code === '23505' && taken) return new Refusal(taken);
  const said = ['42501', '23514', '54000', 'P0002'].includes(error.code);
  const technical = /constraint|permission denied|violates/.test(error.message);
  if (!said || technical) return new Refusal('Sulba couldn’t do that just now. Try again.');
  return new Refusal(/[.!?]$/.test(error.message) ? error.message : `${error.message}.`);
}

/** The workspaces the person is in, by name. */
export async function workspacesOf(client: Client, personId: string): Promise<Workspace[]> {
  const { data, error } = await client
    .from('members')
    .select('role, workspaces!inner(id, name, slug)')
    .eq('person_id', personId);
  if (error) throw refusal(error);
  return data
    .map(({ role, workspaces }) => ({ ...workspaces, role }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

/** The workspace at an address, if the person is in it. */
export async function workspaceAt(
  client: Client,
  personId: string,
  slug: string,
): Promise<Workspace | null> {
  const { data, error } = await client
    .from('members')
    .select('role, workspaces!inner(id, name, slug)')
    .eq('person_id', personId)
    .eq('workspaces.slug', slug)
    .maybeSingle();
  if (error) throw refusal(error);
  return data ? { ...data.workspaces, role: data.role } : null;
}

/** Creates a workspace with the person as its owner, and gives its address. */
export async function createWorkspace(client: Client, name: string, slug: string): Promise<string> {
  const { data, error } = await client.rpc('create_workspace', { name, slug });
  if (error) throw refusal(error, 'That address is taken.');
  return data.slug;
}

export async function renameWorkspace(client: Client, id: string, name: string): Promise<void> {
  const { error } = await client.from('workspaces').update({ name: name.trim() }).eq('id', id);
  if (error) throw refusal(error);
}

export async function deleteWorkspace(client: Client, id: string): Promise<void> {
  const { error } = await client.rpc('delete_workspace', { workspace: id });
  if (error) throw refusal(error);
}

/** The workspace's members, in the order they joined. */
export async function membersOf(client: Client, workspaceId: string): Promise<Member[]> {
  const { data, error } = await client
    .from('members')
    .select('person_id, role, joined_at, people!inner(name, email)')
    .eq('workspace_id', workspaceId)
    .order('joined_at');
  if (error) throw refusal(error);
  return data.map((row) => ({
    personId: row.person_id,
    name: row.people.name,
    email: row.people.email,
    role: row.role,
    joinedAt: row.joined_at,
  }));
}

export async function setRole(
  client: Client,
  workspaceId: string,
  personId: string,
  role: Role,
): Promise<void> {
  const { error } = await client.rpc('set_member_role', {
    workspace: workspaceId,
    person: personId,
    role,
  });
  if (error) throw refusal(error);
}

/** Removes a member, or, given the person's own id, leaves the workspace. */
export async function removeMember(
  client: Client,
  workspaceId: string,
  personId: string,
): Promise<void> {
  const { error } = await client.rpc('remove_member', { workspace: workspaceId, person: personId });
  if (error) throw refusal(error);
}

/** The links that can still be used, newest first. Only admins and owners see any. */
export async function invitationsOf(client: Client, workspaceId: string): Promise<Invitation[]> {
  const { data, error } = await client
    .from('invitations')
    .select('id, role, created_at, expires_at, people(name)')
    .eq('workspace_id', workspaceId)
    .gt('expires_at', new Date().toISOString())
    .order('created_at', { ascending: false });
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    role: row.role,
    madeBy: row.people?.name ?? null,
    createdAt: row.created_at,
    expiresAt: row.expires_at,
  }));
}

/** Makes an invitation link and gives its token, which only this call ever sees. */
export async function invite(client: Client, workspaceId: string, role: Role): Promise<string> {
  const { data, error } = await client.rpc('create_invitation', { workspace: workspaceId, role });
  if (error) throw refusal(error);
  return data;
}

export async function revokeInvitation(client: Client, id: string): Promise<void> {
  const { error } = await client.from('invitations').delete().eq('id', id);
  if (error) throw refusal(error);
}

/** What a link offers, or null once it has expired or been revoked. */
export async function offerOf(client: Client, token: string): Promise<Offer | null> {
  const { data, error } = await client.rpc('invitation', { token });
  if (error) throw refusal(error);
  const [offer] = data;
  return offer ? { workspaceName: offer.workspace_name, role: offer.role } : null;
}

/** Joins the workspace a link is for, and gives its address. */
export async function acceptInvitation(client: Client, token: string): Promise<string> {
  const { data, error } = await client.rpc('accept_invitation', { token });
  if (error) throw refusal(error);
  return data;
}
