// A spec's history in sentences: who did what, read from the changes Postgres logged.
import { type Change, criterionKey, type SpecStatus, statusNames } from '@sulba/data/specs';

export interface Context {
  /** The spec's number, for its criteria's IDs. */
  readonly spec: number;
  /** The workspace's members' names, by id. */
  readonly names: ReadonlyMap<string, string>;
  /** The spec's criteria's numbers, by id, for a change that doesn't carry its number. */
  readonly criteria: ReadonlyMap<string, number>;
}

/** Who made a change. Agents are always named as agents. */
export function whoOf(change: Change): string {
  if (change.actorKind === 'agent') {
    return change.actorName ? `${change.actorName}’s agent` : 'An agent';
  }
  if (change.actorKind === 'system' || change.actorKind === 'github') return 'Sulba';
  return change.actorName ?? 'Someone who has left';
}

function after(change: Change, field: string): unknown {
  return change.changes[field]?.[1];
}

/** Joins parts as a sentence does: "a", "a and b", "a, b and c". */
function list(parts: readonly string[]): string {
  if (parts.length < 2) return parts.join('');
  return `${parts.slice(0, -1).join(', ')} and ${parts.at(-1)}`;
}

/** What the change did, such as "moved it to In review" or "added SPEC-12/AC-3". */
export function whatOf(change: Change, context: Context): string {
  if (change.subjectType === 'criterion') {
    const number =
      (after(change, 'number') as number | null | undefined) ??
      (change.changes.number?.[0] as number | undefined) ??
      context.criteria.get(change.subjectId);
    const which = number ? criterionKey(context.spec, number) : 'a criterion';
    if (change.action === 'criterion.created') return `added ${which}`;
    if (change.action === 'criterion.deleted') return `removed ${which}`;
    return `reworded ${which}`;
  }
  if (change.action === 'spec.created') return 'wrote the spec';
  const parts: string[] = [];
  if ('title' in change.changes) parts.push(`renamed it “${String(after(change, 'title'))}”`);
  if ('status' in change.changes) {
    parts.push(`moved it to ${statusNames[after(change, 'status') as SpecStatus]}`);
  }
  if ('owner_id' in change.changes) {
    const owner = after(change, 'owner_id') as string | null;
    parts.push(
      owner === null
        ? 'left it without an owner'
        : `gave it to ${context.names.get(owner) ?? 'someone'}`,
    );
  }
  if ('body' in change.changes) parts.push('edited its text');
  return parts.length ? list(parts) : 'changed it';
}
