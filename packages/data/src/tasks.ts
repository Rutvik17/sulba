// Tasks: an approved spec split into work that a person, or an agent for its person, takes
// (decision record 61). A task's number in its workspace makes its ID: TASK-7. Its taker hands it
// in with one pull request; only people mark it done or cancel it.
import type { Client } from './client.ts';
import type { Database } from './database.ts';
import { refusal } from './refusal.ts';
import type { SpecStatus } from './specs.ts';

export type TaskRole = Database['public']['Enums']['task_role'];
export type TaskStatus = Database['public']['Enums']['task_status'];

export const taskRoles: readonly TaskRole[] = ['build', 'test', 'review', 'document'];

export const taskRoleNames: Record<TaskRole, string> = {
  build: 'Build',
  test: 'Test',
  review: 'Review',
  document: 'Document',
};

export const taskRoleMeanings: Record<TaskRole, string> = {
  build: 'Write the code',
  test: 'Write the tests that prove its criteria',
  review: 'Review a pull request',
  document: 'Write the documents',
};

export const taskStatuses: readonly TaskStatus[] = [
  'open',
  'in_progress',
  'blocked',
  'in_review',
  'done',
  'canceled',
];

export const taskStatusNames: Record<TaskStatus, string> = {
  open: 'Open',
  in_progress: 'In progress',
  blocked: 'Blocked',
  in_review: 'In review',
  done: 'Done',
  canceled: 'Canceled',
};

/** A task's ID, such as "TASK-7". */
export function taskKey(number: number): string {
  return `TASK-${number}`;
}

/** The number in a task's ID, such as 7 in "TASK-7" or "task-7", or null. */
export function taskNumberOf(key: string): number | null {
  const match = /^task-([1-9]\d{0,8})$/i.exec(key);
  return match ? Number(match[1]) : null;
}

/** What's wrong with a task's title, or null. */
export function taskTitleProblem(title: string): string | null {
  const trimmed = title.trim();
  if (trimmed === '') return 'Say what the task is.';
  if (trimmed.length > 200) return 'A title has at most 200 characters.';
  return null;
}

/** What's wrong with what blocks a task, or null. */
export function blockerProblem(note: string): string | null {
  const trimmed = note.trim();
  if (trimmed === '') return 'Say what blocks it.';
  if (trimmed.length > 2000) return 'A note has at most 2,000 characters.';
  return null;
}

const pullRequest =
  /^https:\/\/github\.com\/[A-Za-z0-9-]{1,100}\/[A-Za-z0-9_.-]{1,100}\/pull\/[1-9]\d{0,9}$/;

/** What's wrong with a pull request's address, or null. */
export function pullRequestProblem(address: string): string | null {
  return pullRequest.test(address.trim())
    ? null
    : 'A pull request’s address looks like https://github.com/owner/repo/pull/12.';
}

/** A pull request's short name, such as "acme-co/booking#12". */
export function pullRequestName(address: string): string {
  const [, , , owner, repository, , number] = address.split('/');
  return `${owner}/${repository}#${number}`;
}

/** A task as a list of tasks shows it. */
export interface TaskSummary {
  readonly id: string;
  readonly number: number;
  readonly title: string;
  readonly role: TaskRole;
  readonly status: TaskStatus;
  readonly spec: { readonly number: number; readonly title: string };
  readonly takenBy: string | null;
  readonly takenByAgent: string | null;
  readonly pullRequest: string | null;
  readonly updatedAt: string;
}

/** A task with everything its page shows. */
export interface Task extends Omit<TaskSummary, 'spec'> {
  readonly body: string;
  readonly note: string | null;
  readonly takenAt: string | null;
  readonly createdBy: string | null;
  readonly createdByAgent: string | null;
  readonly createdAt: string;
  readonly spec: {
    readonly id: string;
    readonly number: number;
    readonly title: string;
    readonly status: SpecStatus;
  };
  /** The spec's criteria it covers, in order. */
  readonly criteria: readonly { readonly number: number; readonly text: string }[];
}

const summary =
  'id, number, title, role, status, taken_by, taken_by_agent, pull_request, updated_at, specs(number, title)';

type SummaryRow = {
  id: string;
  number: number;
  title: string;
  role: TaskRole;
  status: TaskStatus;
  taken_by: string | null;
  taken_by_agent: string | null;
  pull_request: string | null;
  updated_at: string;
  specs: { number: number; title: string };
};

function summaryOf(row: SummaryRow): TaskSummary {
  return {
    id: row.id,
    number: row.number,
    title: row.title,
    role: row.role,
    status: row.status,
    spec: row.specs,
    takenBy: row.taken_by,
    takenByAgent: row.taken_by_agent,
    pullRequest: row.pull_request,
    updatedAt: row.updated_at,
  };
}

/** A workspace's tasks, the newest first. */
export async function tasksOf(client: Client, workspaceId: string): Promise<TaskSummary[]> {
  const { data, error } = await client
    .from('tasks')
    .select(summary)
    .eq('workspace_id', workspaceId)
    .order('number', { ascending: false });
  if (error) throw refusal(error);
  return data.map(summaryOf);
}

/** A spec's tasks, in the order they were written. */
export async function specTasks(client: Client, specId: string): Promise<TaskSummary[]> {
  const { data, error } = await client
    .from('tasks')
    .select(summary)
    .eq('spec_id', specId)
    .order('number');
  if (error) throw refusal(error);
  return data.map(summaryOf);
}

/** The task with this number in the workspace, or null. */
export async function taskAt(
  client: Client,
  workspaceId: string,
  number: number,
): Promise<Task | null> {
  const { data, error } = await client
    .from('tasks')
    .select(
      'id, number, title, role, status, body, note, taken_by, taken_by_agent, taken_at, pull_request, created_by, created_by_agent, created_at, updated_at, specs(id, number, title, status), task_criteria(criteria(number, text))',
    )
    .eq('workspace_id', workspaceId)
    .eq('number', number)
    .maybeSingle();
  if (error) throw refusal(error);
  if (!data) return null;
  return {
    id: data.id,
    number: data.number,
    title: data.title,
    role: data.role,
    status: data.status,
    body: data.body,
    note: data.note,
    takenBy: data.taken_by,
    takenByAgent: data.taken_by_agent,
    takenAt: data.taken_at,
    pullRequest: data.pull_request,
    createdBy: data.created_by,
    createdByAgent: data.created_by_agent,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    spec: data.specs,
    criteria: data.task_criteria
      .map(({ criteria }) => criteria)
      .sort((a, b) => a.number - b.number),
  };
}

/** Writes a task from an approved spec, covering the criteria with these numbers, and gives its number. */
export async function createTask(
  client: Client,
  specId: string,
  task: { title: string; role: TaskRole; body: string; criteria: readonly number[] },
): Promise<number> {
  const { data, error } = await client.rpc('create_task', {
    spec: specId,
    title: task.title.trim(),
    role: task.role,
    body: task.body.trim(),
    criteria: [...task.criteria],
  });
  if (error) throw refusal(error);
  return data;
}

/** What can be edited about a task. */
export interface TaskChange {
  readonly title?: string;
  readonly role?: TaskRole;
  readonly body?: string;
}

export async function updateTask(client: Client, id: string, change: TaskChange): Promise<void> {
  const { error } = await client
    .from('tasks')
    .update({
      ...(change.title === undefined ? {} : { title: change.title.trim() }),
      ...(change.role === undefined ? {} : { role: change.role }),
      ...(change.body === undefined ? {} : { body: change.body }),
    })
    .eq('id', id);
  if (error) throw refusal(error);
}

/** Moves a task on: takes it, blocks it with a note, hands it in with its pull request, and so on. */
export async function moveTask(
  client: Client,
  id: string,
  status: TaskStatus,
  { note, pullRequest }: { note?: string; pullRequest?: string } = {},
): Promise<void> {
  const { error } = await client.rpc('update_task', {
    task: id,
    status,
    ...(note === undefined ? {} : { note: note.trim() }),
    ...(pullRequest === undefined ? {} : { pull_request: pullRequest.trim() }),
  });
  if (error) throw refusal(error);
}
