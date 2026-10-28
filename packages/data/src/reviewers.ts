// A spec's reviewers and what each answered (decision record 52). Members name them; a spec with
// reviewers is approved when the last of them approves it, and a change to a spec in review asks
// those who approved it to review it again.
import type { Client } from './client.ts';
import type { Database } from './database.ts';
import { refusal } from './refusal.ts';
import type { SpecStatus } from './specs.ts';

export type Verdict = Database['public']['Enums']['review_verdict'];

export const verdictNames: Record<Verdict, string> = {
  pending: 'Waiting',
  approved: 'Approved',
  changes_requested: 'Asked for changes',
};

/** The most a reviewer's note can hold, as Postgres checks it. */
export const noteLimit = 2000;

/** A spec has at most this many reviewers. */
export const reviewerLimit = 10;

export interface Review {
  readonly id: string;
  readonly specId: string;
  readonly reviewerId: string;
  readonly requestedBy: string | null;
  readonly requestedAt: string;
  readonly verdict: Verdict;
  /** What the reviewer said with their answer. */
  readonly note: string | null;
  readonly answeredAt: string | null;
}

/** Where a spec's review stands, such as "1 of 2 approved". */
export function standingOf(reviews: readonly Pick<Review, 'verdict'>[]): string {
  if (reviews.length === 0) return 'No reviewers';
  const approved = reviews.filter((review) => review.verdict === 'approved').length;
  const asked = reviews.filter((review) => review.verdict === 'changes_requested').length;
  const standing = `${approved} of ${reviews.length} approved`;
  return asked ? `${standing}, ${asked} asked for changes` : standing;
}

/** What's wrong with a review's answer, or null. */
export function answerProblem(verdict: Exclude<Verdict, 'pending'>, note: string): string | null {
  const trimmed = note.trim();
  if (verdict === 'changes_requested' && trimmed === '') return 'Say what to change.';
  if (trimmed.length > noteLimit)
    return `A note has at most ${noteLimit.toLocaleString('en')} characters.`;
  return null;
}

/** The spec's reviewers, in the order they were asked. */
export async function reviewsOf(client: Client, specId: string): Promise<Review[]> {
  const { data, error } = await client
    .from('spec_reviews')
    .select('id, spec_id, reviewer_id, requested_by, requested_at, verdict, note, answered_at')
    .eq('spec_id', specId)
    .order('requested_at');
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    specId: row.spec_id,
    reviewerId: row.reviewer_id,
    requestedBy: row.requested_by,
    requestedAt: row.requested_at,
    verdict: row.verdict,
    note: row.note,
    answeredAt: row.answered_at,
  }));
}

/** A review with its reviewer's name, as an agent reads it. */
export interface NamedReview {
  readonly reviewer: string;
  readonly verdict: Verdict;
  readonly note: string | null;
}

/** The spec's reviewers by name, in the order they were asked. */
export async function namedReviewsOf(client: Client, specId: string): Promise<NamedReview[]> {
  const { data, error } = await client
    .from('spec_reviews')
    .select('verdict, note, people!spec_reviews_reviewer_id_fkey(name, email)')
    .eq('spec_id', specId)
    .order('requested_at');
  if (error) throw refusal(error);
  return data.map((row) => ({
    reviewer: row.people.name || row.people.email || 'Someone',
    verdict: row.verdict,
    note: row.note,
  }));
}

/** Asks someone in the workspace to review the spec, or asks a reviewer again. */
export async function requestReview(
  client: Client,
  specId: string,
  reviewerId: string,
): Promise<void> {
  const { error } = await client.rpc('request_review', { spec: specId, reviewer: reviewerId });
  if (error) throw refusal(error);
}

export async function removeReviewer(
  client: Client,
  specId: string,
  reviewerId: string,
): Promise<void> {
  const { error } = await client.rpc('remove_reviewer', { spec: specId, reviewer: reviewerId });
  if (error) throw refusal(error);
}

/** Answers a review, and gives the spec's status, which the last approval makes Approved. */
export async function reviewSpec(
  client: Client,
  specId: string,
  verdict: Exclude<Verdict, 'pending'>,
  note: string,
): Promise<SpecStatus> {
  const trimmed = note.trim();
  const { data, error } = await client.rpc('review_spec', {
    spec: specId,
    verdict,
    ...(trimmed ? { note: trimmed } : {}),
  });
  if (error) throw refusal(error);
  return data;
}
