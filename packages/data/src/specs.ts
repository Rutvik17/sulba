// Specs and their acceptance criteria (decision record 49). A spec's number in its workspace and
// a criterion's number in its spec make the IDs people, branches and tests use: SPEC-12/AC-3.
import type { Client } from './client.ts';
import type { Database, Json } from './database.ts';
import { refusal } from './refusal.ts';

export type SpecStatus = Database['public']['Enums']['spec_status'];
export type ActorKind = Database['public']['Enums']['actor_kind'];

/** Every status, in the order a spec usually moves through them. */
export const specStatuses: readonly SpecStatus[] = [
  'draft',
  'in_review',
  'approved',
  'implemented',
  'abandoned',
  'superseded',
];

export const statusNames: Record<SpecStatus, string> = {
  draft: 'Draft',
  in_review: 'In review',
  approved: 'Approved',
  implemented: 'Implemented',
  abandoned: 'Abandoned',
  superseded: 'Superseded',
};

export const statusMeanings: Record<SpecStatus, string> = {
  draft: 'Still being written',
  in_review: 'Written, and waiting for the team to agree it',
  approved: 'Agreed, and ready to build',
  implemented: 'Built and merged',
  abandoned: 'Won’t be built',
  superseded: 'Replaced by another spec',
};

/** The most a spec's text can hold, as Postgres checks it. */
export const bodyLimit = 50_000;

/** A spec's ID, such as "SPEC-12". */
export function specKey(number: number): string {
  return `SPEC-${number}`;
}

/** A criterion's ID, such as "SPEC-12/AC-3", which a test puts in its name to claim it. */
export function criterionKey(spec: number, criterion: number): string {
  return `${specKey(spec)}/AC-${criterion}`;
}

/** The number in a spec's ID, such as 12 in "SPEC-12" or "spec-12", or null. */
export function specNumberOf(key: string): number | null {
  const match = /^spec-([1-9]\d{0,8})$/i.exec(key);
  return match ? Number(match[1]) : null;
}

/** What's wrong with a spec's title, or null. */
export function titleProblem(title: string): string | null {
  const trimmed = title.trim();
  if (trimmed === '') return 'Give the spec a title.';
  if (trimmed.length > 200) return 'A title has at most 200 characters.';
  return null;
}

/** What's wrong with a criterion's wording, or null. */
export function criterionProblem(text: string): string | null {
  const trimmed = text.trim();
  if (trimmed === '') return 'Write what must be true.';
  if (trimmed.length > 1000) return 'A criterion has at most 1,000 characters.';
  return null;
}

/** A spec as the list of specs shows it. */
export interface SpecSummary {
  readonly id: string;
  readonly number: number;
  readonly title: string;
  readonly status: SpecStatus;
  readonly ownerId: string | null;
  /** How many criteria it has. */
  readonly criteria: number;
  readonly updatedAt: string;
}

export interface Criterion {
  readonly id: string;
  readonly number: number;
  readonly text: string;
}

export interface Spec {
  readonly id: string;
  readonly number: number;
  readonly title: string;
  readonly status: SpecStatus;
  /** Markdown. */
  readonly body: string;
  readonly ownerId: string | null;
  readonly createdAt: string;
  readonly updatedAt: string;
  /** In the order they were added. */
  readonly criteria: readonly Criterion[];
}

/** One change in a spec's history: to the spec or one of its criteria. */
export interface Change {
  readonly id: number;
  readonly at: string;
  readonly actorKind: ActorKind;
  /** Who acted, while they're still in the workspace. */
  readonly actorName: string | null;
  readonly action: string;
  readonly subjectType: string;
  readonly subjectId: string;
  /** Each field that changed as [before, after], or null when its values aren't kept. */
  readonly changes: Readonly<Record<string, readonly [Json, Json] | null>>;
}

/** The workspace's specs, newest first. */
export async function specsOf(client: Client, workspaceId: string): Promise<SpecSummary[]> {
  const { data, error } = await client
    .from('specs')
    .select('id, number, title, status, owner_id, updated_at, criteria(count)')
    .eq('workspace_id', workspaceId)
    .order('number', { ascending: false });
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    number: row.number,
    title: row.title,
    status: row.status,
    ownerId: row.owner_id,
    criteria: row.criteria[0]?.count ?? 0,
    updatedAt: row.updated_at,
  }));
}

/** The spec with a number in the workspace, with its criteria, or null when there's none. */
export async function specAt(
  client: Client,
  workspaceId: string,
  number: number,
): Promise<Spec | null> {
  const { data, error } = await client
    .from('specs')
    .select(
      'id, number, title, status, body, owner_id, created_at, updated_at, criteria(id, number, text)',
    )
    .eq('workspace_id', workspaceId)
    .eq('number', number)
    .order('number', { referencedTable: 'criteria' })
    .maybeSingle();
  if (error) throw refusal(error);
  if (!data) return null;
  return {
    id: data.id,
    number: data.number,
    title: data.title,
    status: data.status,
    body: data.body,
    ownerId: data.owner_id,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    criteria: data.criteria,
  };
}

/** Writes a spec with its first criteria, owned by the person who writes it, and gives its number. */
export async function createSpec(
  client: Client,
  workspaceId: string,
  title: string,
  criteria: readonly string[],
): Promise<number> {
  const { data, error } = await client.rpc('create_spec', {
    workspace: workspaceId,
    title: title.trim(),
    criteria: criteria.map((text) => text.trim()).filter((text) => text !== ''),
  });
  if (error) throw refusal(error);
  return data;
}

/** What can change about a spec. */
export interface SpecChange {
  readonly title?: string;
  readonly status?: SpecStatus;
  readonly body?: string;
  readonly ownerId?: string | null;
}

export async function updateSpec(client: Client, id: string, change: SpecChange): Promise<void> {
  const { error } = await client
    .from('specs')
    .update({
      ...(change.title === undefined ? {} : { title: change.title.trim() }),
      ...(change.status === undefined ? {} : { status: change.status }),
      ...(change.body === undefined ? {} : { body: change.body }),
      ...(change.ownerId === undefined ? {} : { owner_id: change.ownerId }),
    })
    .eq('id', id);
  if (error) throw refusal(error);
}

/** Adds a criterion at the end of a spec, and gives its number. */
export async function addCriterion(client: Client, specId: string, text: string): Promise<number> {
  const { data, error } = await client.rpc('add_criterion', { spec: specId, text: text.trim() });
  if (error) throw refusal(error);
  return data;
}

export async function rewordCriterion(client: Client, id: string, text: string): Promise<void> {
  const { error } = await client.from('criteria').update({ text: text.trim() }).eq('id', id);
  if (error) throw refusal(error);
}

/** Removes a criterion. Its number isn't given to another. */
export async function removeCriterion(client: Client, id: string): Promise<void> {
  const { error } = await client.from('criteria').delete().eq('id', id);
  if (error) throw refusal(error);
}

/** The spec's history and its criteria's, newest first: at most the last 100 changes. */
export async function historyOf(
  client: Client,
  workspaceId: string,
  specId: string,
): Promise<Change[]> {
  const { data, error } = await client
    .from('events')
    .select('id, at, actor_kind, action, subject_type, subject_id, changes, people(name)')
    .eq('workspace_id', workspaceId)
    .eq('spec_id', specId)
    .order('id', { ascending: false })
    .limit(100);
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    at: row.at,
    actorKind: row.actor_kind,
    actorName: row.people?.name || null,
    action: row.action,
    subjectType: row.subject_type,
    subjectId: row.subject_id,
    changes: row.changes as Change['changes'],
  }));
}
