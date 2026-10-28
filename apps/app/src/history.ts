// A spec's history in sentences: who did what, read from the changes Postgres logged.
import { type Change, criterionKey, type SpecStatus, statusNames } from '@sulba/data/specs';

export interface Context {
  /** The spec's number, for its criteria's IDs. */
  readonly spec: number;
  /** The workspace's members' names, by id. */
  readonly names: ReadonlyMap<string, string>;
  /** The spec's criteria's numbers, by id, for a change that doesn't carry its number. */
  readonly criteria: ReadonlyMap<string, number>;
  /** Who each of the spec's reviews is from, by its id, for a change that doesn't say. */
  readonly reviewers: ReadonlyMap<string, string>;
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

/** What a change to one of the spec's reviews did, such as "asked Ben to review it". */
function reviewOf(change: Change, context: Context): string {
  const reviewer =
    (after(change, 'reviewer_id') as string | null | undefined) ??
    (change.changes.reviewer_id?.[0] as string | undefined) ??
    context.reviewers.get(change.subjectId);
  const name = (reviewer && context.names.get(reviewer)) || 'someone who has left';
  if (change.action === 'review.created') return `asked ${name} to review it`;
  if (change.action === 'review.deleted') return `took ${name} off its reviewers`;
  const verdict = after(change, 'verdict');
  if (verdict === 'approved') return 'approved it';
  if (verdict === 'changes_requested') return 'asked for changes';
  if (verdict === 'pending') return `asked ${name} to review it again`;
  return 'changed a review';
}

/** What the change did, such as "moved it to In review" or "added SPEC-12/AC-3". */
export function whatOf(change: Change, context: Context): string {
  if (change.subjectType === 'review') return reviewOf(change, context);
  if (change.subjectType === 'criterion') {
    const number =
      (after(change, 'number') as number | null | undefined) ??
      (change.changes.number?.[0] as number | undefined) ??
      context.criteria.get(change.subjectId);
    const which = number ? criterionKey(context.spec, number) : 'a criterion';
    if (change.action === 'criterion.created') return `added ${which}`;
    if (change.action === 'criterion.deleted') return `removed ${which}`;
    if (!('text' in change.changes) && after(change, 'suspect_since') === null) {
      return `confirmed that ${which}’s tests check its wording`;
    }
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
