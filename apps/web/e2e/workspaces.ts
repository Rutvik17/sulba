import type { Page, Route } from '@playwright/test';
import { learner, supabase } from './supabase';

// Stands in for the workspace tables and the functions that change them (decision record 48),
// answering as PostgREST does, so the app's pages can be tested without a database. Postgres
// decides who may do what; the stand-in keeps only the rules a page shows the person.

export type Role = 'viewer' | 'member' | 'admin' | 'owner';

export interface Person {
  readonly id: string;
  readonly name: string;
  readonly email: string;
}

export interface Workspace {
  readonly id: string;
  name: string;
  readonly slug: string;
}

export interface Membership {
  readonly workspace: string;
  readonly person: string;
  role: Role;
  readonly joinedAt: string;
}

export interface Link {
  readonly id: string;
  readonly workspace: string;
  readonly role: Role;
  readonly token: string;
  readonly createdBy: string;
  readonly createdAt: string;
  readonly expiresAt: string;
}

export interface Team {
  readonly people: Person[];
  readonly workspaces: Workspace[];
  readonly members: Membership[];
  readonly invitations: Link[];
}

/** The signed-in learner, as the people table holds them. */
export const ada: Person = { id: learner.id, name: 'Ada Lovelace', email: learner.email };
export const ben: Person = {
  id: 'a0000000-0000-4000-8000-000000000002',
  name: 'Ben Ortiz',
  email: 'ben@example.com',
};

export const acme: Workspace = {
  id: 'b0000000-0000-4000-8000-000000000001',
  name: 'Acme',
  slug: 'acme',
};

const week = 7 * 24 * 60 * 60 * 1000;

/** An invitation link made a day ago, which lasts another six days. */
export function link(workspace: Workspace, token: string, role: Role = 'member'): Link {
  const made = Date.now() - 24 * 60 * 60 * 1000;
  return {
    id: `c0000000-0000-4000-8000-${token.slice(0, 12).padStart(12, '0')}`,
    workspace: workspace.id,
    role,
    token,
    createdBy: ada.id,
    createdAt: new Date(made).toISOString(),
    expiresAt: new Date(made + week).toISOString(),
  };
}

/** A team of the given workspaces, each with the given members. */
export function team({
  people = [ada, ben],
  workspaces = [],
  members = [],
  invitations = [],
}: Partial<Team> = {}): Team {
  return {
    people: [...people],
    workspaces: workspaces.map((workspace) => ({ ...workspace })),
    members: members.map((member) => ({ ...member })),
    invitations: [...invitations],
  };
}

export function member(workspace: Workspace, person: Person, role: Role): Membership {
  return { workspace: workspace.id, person: person.id, role, joinedAt: '2026-10-20T09:00:00Z' };
}

/** Every function the page called, with what it sent. */
export interface TeamCalls {
  readonly rpc: { readonly name: string; readonly args: Record<string, unknown> }[];
}

const cors = {
  'access-control-allow-origin': '*',
  'access-control-allow-headers': '*',
  'access-control-allow-methods': 'GET, POST, PATCH, DELETE, OPTIONS',
};

function answer(route: Route, status: number, body?: unknown) {
  return route.fulfill({
    status,
    headers: { ...cors, 'content-type': 'application/json' },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
}

/** PostgREST's answer when a function raises an exception for people to read. */
function refuse(route: Route, code: string, message: string) {
  return answer(route, 400, { code, message, details: null, hint: null });
}

/** The value of a PostgREST filter such as `person_id=eq.<id>`. */
function equal(url: URL, column: string): string | null {
  const filter = url.searchParams.get(column);
  return filter?.startsWith('eq.') ? filter.slice(3) : null;
}

/** Stands in for the workspace tables and functions, on top of standIn's sign-in. */
export async function standInTeam(page: Page, held: Team): Promise<TeamCalls> {
  const calls: TeamCalls = { rpc: [] };
  const person = (id: string) => held.people.find((each) => each.id === id);
  const owners = (workspace: string) =>
    held.members.filter((each) => each.workspace === workspace && each.role === 'owner');

  await page.route(`${supabase}/rest/v1/members**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const url = new URL(route.request().url());
    const personId = equal(url, 'person_id');
    if (personId) {
      const slug = equal(url, 'workspaces.slug');
      const rows = held.members
        .filter((each) => each.person === personId)
        .map((each) => ({
          role: each.role,
          workspaces: held.workspaces.find((workspace) => workspace.id === each.workspace),
        }))
        .filter((row) => row.workspaces && (slug === null || row.workspaces.slug === slug));
      return answer(route, 200, rows);
    }
    const workspaceId = equal(url, 'workspace_id');
    const rows = held.members
      .filter((each) => each.workspace === workspaceId)
      .sort((a, b) => a.joinedAt.localeCompare(b.joinedAt))
      .map((each) => {
        const { name, email } = person(each.person) ?? { name: '', email: null };
        return {
          person_id: each.person,
          role: each.role,
          joined_at: each.joinedAt,
          people: { name, email },
        };
      });
    return answer(route, 200, rows);
  });

  await page.route(`${supabase}/rest/v1/workspaces**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const workspace = held.workspaces.find(
      (each) => each.id === equal(new URL(route.request().url()), 'id'),
    );
    if (workspace) workspace.name = (route.request().postDataJSON() as { name: string }).name;
    return answer(route, 204);
  });

  await page.route(`${supabase}/rest/v1/invitations**`, (route) => {
    const method = route.request().method();
    if (method === 'OPTIONS') return answer(route, 204);
    const url = new URL(route.request().url());
    if (method === 'DELETE') {
      const at = held.invitations.findIndex((each) => each.id === equal(url, 'id'));
      if (at >= 0) held.invitations.splice(at, 1);
      return answer(route, 204);
    }
    const rows = held.invitations
      .filter((each) => each.workspace === equal(url, 'workspace_id'))
      .filter((each) => Date.parse(each.expiresAt) > Date.now())
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
      .map((each) => ({
        id: each.id,
        role: each.role,
        created_at: each.createdAt,
        expires_at: each.expiresAt,
        people: person(each.createdBy) ? { name: person(each.createdBy)?.name } : null,
      }));
    return answer(route, 200, rows);
  });

  await page.route(`${supabase}/rest/v1/rpc/**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const name = new URL(route.request().url()).pathname.split('/').at(-1) ?? '';
    const args = (route.request().postDataJSON() ?? {}) as Record<string, string>;
    calls.rpc.push({ name, args });
    const open = (token: string) =>
      held.invitations.find(
        (each) => each.token === token && Date.parse(each.expiresAt) > Date.now(),
      );

    switch (name) {
      case 'create_workspace': {
        const slug = args.slug ?? '';
        if (held.workspaces.some((each) => each.slug === slug)) {
          return answer(route, 409, {
            code: '23505',
            message: 'duplicate key value violates unique constraint "workspaces_slug_key"',
            details: null,
            hint: null,
          });
        }
        const workspace = { id: crypto.randomUUID(), name: args.name ?? '', slug };
        held.workspaces.push(workspace);
        held.members.push({
          workspace: workspace.id,
          person: ada.id,
          role: 'owner',
          joinedAt: new Date().toISOString(),
        });
        return answer(route, 200, { ...workspace, created_at: new Date().toISOString() });
      }
      case 'create_invitation': {
        const token = crypto.randomUUID().replaceAll('-', '').repeat(2);
        const workspace = held.workspaces.find((each) => each.id === args.workspace);
        if (workspace) {
          held.invitations.push({
            ...link(workspace, token, args.role as Role),
            createdAt: new Date().toISOString(),
            expiresAt: new Date(Date.now() + week).toISOString(),
          });
        }
        return answer(route, 200, token);
      }
      case 'invitation': {
        const found = open(args.token ?? '');
        const workspace = held.workspaces.find((each) => each.id === found?.workspace);
        return answer(
          route,
          200,
          found && workspace ? [{ workspace_name: workspace.name, role: found.role }] : [],
        );
      }
      case 'accept_invitation': {
        const found = open(args.token ?? '');
        const workspace = held.workspaces.find((each) => each.id === found?.workspace);
        if (!found || !workspace) {
          return refuse(route, 'P0002', 'This invitation has expired or been revoked');
        }
        if (
          !held.members.some((each) => each.workspace === workspace.id && each.person === ada.id)
        ) {
          held.members.push({
            workspace: workspace.id,
            person: ada.id,
            role: found.role,
            joinedAt: new Date().toISOString(),
          });
        }
        return answer(route, 200, workspace.slug);
      }
      case 'set_member_role':
      case 'remove_member': {
        const at = held.members.findIndex(
          (each) => each.workspace === args.workspace && each.person === args.person,
        );
        const target = held.members[at];
        if (!target) return refuse(route, 'P0002', 'They aren’t a member of this workspace');
        const lastOwner = target.role === 'owner' && owners(target.workspace).length === 1;
        if (lastOwner && (name === 'remove_member' || args.role !== 'owner')) {
          return refuse(
            route,
            '23514',
            'A workspace needs an owner: make someone else an owner first',
          );
        }
        if (name === 'remove_member') held.members.splice(at, 1);
        else target.role = args.role as Role;
        return answer(route, 204);
      }
      case 'delete_workspace': {
        const id = args.workspace;
        held.workspaces.splice(
          held.workspaces.findIndex((each) => each.id === id),
          1,
        );
        for (let at = held.members.length - 1; at >= 0; at--) {
          if (held.members[at]?.workspace === id) held.members.splice(at, 1);
        }
        return answer(route, 204);
      }
      default:
        return route.abort();
    }
  });

  return calls;
}
