// Requests: what someone wants built, in their own words, before it's written as specs (decision
// record 60). A request's number in its workspace makes its ID: REQ-3. An agent asks its writer
// questions about it and drafts specs from it; only people answer, and decide it's planned or
// closed.
import type { Client } from './client.ts';
import type { Database } from './database.ts';
import { refusal } from './refusal.ts';
import type { SpecStatus } from './specs.ts';

export type RequestStatus = Database['public']['Enums']['request_status'];

export const requestStatuses: readonly RequestStatus[] = ['open', 'planned', 'closed'];

export const requestStatusNames: Record<RequestStatus, string> = {
  open: 'Open',
  planned: 'Planned',
  closed: 'Closed',
};

export const requestStatusMeanings: Record<RequestStatus, string> = {
  open: 'Being worked out into specs',
  planned: 'Its specs are the plan',
  closed: 'Won’t be built',
};

/** A request's ID, such as "REQ-3". */
export function requestKey(number: number): string {
  return `REQ-${number}`;
}

/** The number in a request's ID, such as 3 in "REQ-3" or "req-3", or null. */
export function requestNumberOf(key: string): number | null {
  const match = /^req-([1-9]\d{0,8})$/i.exec(key);
  return match ? Number(match[1]) : null;
}

/** What's wrong with a request's title, or null. */
export function requestTitleProblem(title: string): string | null {
  const trimmed = title.trim();
  if (trimmed === '') return 'Say what you want built.';
  if (trimmed.length > 200) return 'A title has at most 200 characters.';
  return null;
}

/** What's wrong with an answer, or null. */
export function answerProblem(answer: string): string | null {
  const trimmed = answer.trim();
  if (trimmed === '') return 'Write an answer.';
  if (trimmed.length > 5000) return 'An answer has at most 5,000 characters.';
  return null;
}

/** Who asked a question: "Ben Ortiz’s agent, Claude Code", or "Ben Ortiz" when a person asked. */
export function askerName(person: string | null | undefined, agent: string | null): string {
  const who = person || 'Someone who has left';
  return agent ? `${who}’s agent, ${agent}` : who;
}

/** A request as the list of requests shows it. */
export interface RequestSummary {
  readonly id: string;
  readonly number: number;
  readonly title: string;
  readonly status: RequestStatus;
  readonly createdBy: string | null;
  /** How many of its questions wait for an answer. */
  readonly unanswered: number;
  /** How many specs were drafted from it. */
  readonly specs: number;
  readonly updatedAt: string;
}

export interface Question {
  readonly id: string;
  readonly text: string;
  readonly answer: string | null;
  readonly askedBy: string | null;
  /** The agent that asked for its person, by the name it registered, or null when a person asked. */
  readonly askedByAgent: string | null;
  readonly answeredBy: string | null;
  readonly askedAt: string;
  readonly answeredAt: string | null;
}

/** A spec drafted from a request. */
export interface DraftedSpec {
  readonly number: number;
  readonly title: string;
  readonly status: SpecStatus;
}

export interface Request {
  readonly id: string;
  readonly number: number;
  readonly title: string;
  readonly status: RequestStatus;
  /** Markdown. */
  readonly body: string;
  readonly createdBy: string | null;
  readonly createdAt: string;
  readonly updatedAt: string;
  /** In the order they were asked. */
  readonly questions: readonly Question[];
  /** In the order they were written. */
  readonly specs: readonly DraftedSpec[];
}

/** The workspace's requests, newest first. */
export async function requestsOf(client: Client, workspaceId: string): Promise<RequestSummary[]> {
  const { data, error } = await client
    .from('requests')
    .select('id, number, title, status, created_by, updated_at, questions(answer), specs(count)')
    .eq('workspace_id', workspaceId)
    .order('number', { ascending: false });
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    number: row.number,
    title: row.title,
    status: row.status,
    createdBy: row.created_by,
    unanswered: row.questions.filter((question) => question.answer === null).length,
    specs: row.specs[0]?.count ?? 0,
    updatedAt: row.updated_at,
  }));
}

/** The request with a number in the workspace, with its questions and specs, or null. */
export async function requestAt(
  client: Client,
  workspaceId: string,
  number: number,
): Promise<Request | null> {
  const { data, error } = await client
    .from('requests')
    .select(
      'id, number, title, status, body, created_by, created_at, updated_at, questions(id, text, answer, asked_by, asked_by_agent, answered_by, asked_at, answered_at), specs(number, title, status)',
    )
    .eq('workspace_id', workspaceId)
    .eq('number', number)
    .order('asked_at', { referencedTable: 'questions' })
    .order('number', { referencedTable: 'specs' })
    .maybeSingle();
  if (error) throw refusal(error);
  if (!data) return null;
  return {
    id: data.id,
    number: data.number,
    title: data.title,
    status: data.status,
    body: data.body,
    createdBy: data.created_by,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    questions: data.questions.map((question) => ({
      id: question.id,
      text: question.text,
      answer: question.answer,
      askedBy: question.asked_by,
      askedByAgent: question.asked_by_agent,
      answeredBy: question.answered_by,
      askedAt: question.asked_at,
      answeredAt: question.answered_at,
    })),
    specs: data.specs,
  };
}

/** Writes a request and gives its number. */
export async function createRequest(
  client: Client,
  workspaceId: string,
  title: string,
  body: string,
): Promise<number> {
  const { data, error } = await client.rpc('create_request', {
    workspace: workspaceId,
    title: title.trim(),
    body: body.trim(),
  });
  if (error) throw refusal(error);
  return data;
}

/** What can change about a request. */
export interface RequestChange {
  readonly title?: string;
  readonly status?: RequestStatus;
  readonly body?: string;
}

export async function updateRequest(
  client: Client,
  id: string,
  change: RequestChange,
): Promise<void> {
  const { error } = await client
    .from('requests')
    .update({
      ...(change.title === undefined ? {} : { title: change.title.trim() }),
      ...(change.status === undefined ? {} : { status: change.status }),
      ...(change.body === undefined ? {} : { body: change.body }),
    })
    .eq('id', id);
  if (error) throw refusal(error);
}

/** Asks a request's writer a question, and gives its ID. */
export async function askQuestion(
  client: Client,
  requestId: string,
  text: string,
): Promise<string> {
  const { data, error } = await client.rpc('ask_question', {
    request: requestId,
    text: text.trim(),
  });
  if (error) throw refusal(error);
  return data;
}

/** Answers a question, or changes its answer. */
export async function answerQuestion(
  client: Client,
  questionId: string,
  answer: string,
): Promise<void> {
  const { error } = await client.rpc('answer_question', {
    question: questionId,
    answer: answer.trim(),
  });
  if (error) throw refusal(error);
}
