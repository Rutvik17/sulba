// What needs a person in a workspace now, as My work shows it: the questions waiting on the open
// requests they wrote, the tasks handed in or blocked on the specs they own, the specs they've been
// asked to review, the specs they own that aren't built yet, and the criteria failing on their
// specs.
import type { Client } from './client.ts';
import { type CriterionProof, failingOn } from './evidence.ts';
import { refusal } from './refusal.ts';
import type { Verdict } from './reviewers.ts';
import type { SpecStatus } from './specs.ts';
import type { TaskStatus } from './tasks.ts';

/** A question on an open request the person wrote, waiting for their answer. */
export interface Waiting {
  readonly id: string;
  readonly text: string;
  readonly requestNumber: number;
  readonly requestTitle: string;
  readonly askedBy: string | null;
  readonly askedByAgent: string | null;
  readonly askedAt: string;
}

/** A task on a spec the person owns, handed in for review or blocked. */
export interface Handed {
  readonly id: string;
  readonly number: number;
  readonly title: string;
  readonly status: TaskStatus;
  /** Why it's blocked, or what its taker said when handing it in. */
  readonly note: string | null;
  readonly pullRequest: string | null;
  readonly takenBy: string | null;
  readonly takenByAgent: string | null;
  readonly updatedAt: string;
  readonly specNumber: number;
}

/** A spec the person has been asked to review, or to review again since it changed. */
export interface Asked {
  readonly specId: string;
  readonly specNumber: number;
  readonly specTitle: string;
  readonly ownerId: string | null;
  readonly requestedBy: string | null;
  readonly requestedAt: string;
  /** Whether they asked for changes and the spec has changed since. */
  readonly changedSinceAnswer: boolean;
}

/** A spec the person owns that hasn't been built, with its reviewers' answers. */
export interface Owned {
  readonly id: string;
  readonly number: number;
  readonly title: string;
  readonly status: SpecStatus;
  readonly updatedAt: string;
  readonly verdicts: readonly Verdict[];
}

export interface Work {
  readonly questions: readonly Waiting[];
  readonly tasks: readonly Handed[];
  readonly asked: readonly Asked[];
  readonly owned: readonly Owned[];
  readonly failing: readonly CriterionProof[];
}

export async function workOf(client: Client, workspaceId: string, personId: string): Promise<Work> {
  const [questions, tasks, reviews, specs, failing] = await Promise.all([
    client
      .from('questions')
      .select(
        'id, text, asked_by, asked_by_agent, asked_at, requests!inner(number, title, status, created_by)',
      )
      .eq('workspace_id', workspaceId)
      .is('answer', null)
      .eq('requests.created_by', personId)
      .eq('requests.status', 'open')
      .order('asked_at'),
    client
      .from('tasks')
      .select(
        'id, number, title, status, note, pull_request, taken_by, taken_by_agent, updated_at, specs!inner(number, owner_id)',
      )
      .eq('workspace_id', workspaceId)
      .in('status', ['in_review', 'blocked'])
      .eq('specs.owner_id', personId)
      .order('updated_at'),
    client
      .from('spec_reviews')
      .select(
        'verdict, requested_by, requested_at, answered_at, specs!inner(id, number, title, status, owner_id, updated_at)',
      )
      .eq('workspace_id', workspaceId)
      .eq('reviewer_id', personId)
      .in('verdict', ['pending', 'changes_requested'])
      .eq('specs.status', 'in_review')
      .order('requested_at'),
    client
      .from('specs')
      .select('id, number, title, status, updated_at, spec_reviews(verdict)')
      .eq('workspace_id', workspaceId)
      .eq('owner_id', personId)
      .in('status', ['draft', 'in_review', 'approved'])
      .order('updated_at', { ascending: false })
      .limit(50),
    failingOn(client, workspaceId, personId),
  ]);
  if (questions.error) throw refusal(questions.error);
  if (tasks.error) throw refusal(tasks.error);
  if (reviews.error) throw refusal(reviews.error);
  if (specs.error) throw refusal(specs.error);
  return {
    questions: questions.data.map((row) => ({
      id: row.id,
      text: row.text,
      requestNumber: row.requests.number,
      requestTitle: row.requests.title,
      askedBy: row.asked_by,
      askedByAgent: row.asked_by_agent,
      askedAt: row.asked_at,
    })),
    tasks: tasks.data.map((row) => ({
      id: row.id,
      number: row.number,
      title: row.title,
      status: row.status,
      note: row.note,
      pullRequest: row.pull_request,
      takenBy: row.taken_by,
      takenByAgent: row.taken_by_agent,
      updatedAt: row.updated_at,
      specNumber: row.specs.number,
    })),
    asked: reviews.data
      .map((row) => ({
        specId: row.specs.id,
        specNumber: row.specs.number,
        specTitle: row.specs.title,
        ownerId: row.specs.owner_id,
        requestedBy: row.requested_by,
        requestedAt: row.requested_at,
        changedSinceAnswer:
          row.verdict === 'changes_requested' &&
          row.answered_at !== null &&
          Date.parse(row.specs.updated_at) > Date.parse(row.answered_at),
        waiting: row.verdict === 'pending',
      }))
      .filter((row) => row.waiting || row.changedSinceAnswer)
      .map(({ waiting: _, ...row }) => row),
    owned: specs.data.map((row) => ({
      id: row.id,
      number: row.number,
      title: row.title,
      status: row.status,
      updatedAt: row.updated_at,
      verdicts: row.spec_reviews.map((review) => review.verdict),
    })),
    failing,
  };
}
