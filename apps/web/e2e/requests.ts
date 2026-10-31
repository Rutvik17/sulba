import type { Page } from '@playwright/test';
import type { HeldSpec } from './specs';
import { supabase } from './supabase';
import { ada, answer, equal, refuse } from './workspaces';

// Stands in for requests and their questions, and their functions, as PostgREST answers them
// (decision record 60). Call it after standInSpecs, whose empty questions table it takes over.

export type RequestStatus = 'open' | 'planned' | 'closed';

export interface HeldRequest {
  readonly id: string;
  readonly workspace: string;
  readonly number: number;
  title: string;
  status: RequestStatus;
  body: string;
  readonly createdBy: string | null;
  readonly createdAt: string;
  updatedAt: string;
}

export interface HeldQuestion {
  readonly id: string;
  readonly request: string;
  readonly text: string;
  answer: string | null;
  readonly askedBy: string | null;
  readonly askedByAgent: string | null;
  answeredBy: string | null;
  readonly askedAt: string;
  answeredAt: string | null;
}

/** A request of the workspace's, written a day ago by Ada. */
export function request(
  workspace: { id: string },
  number: number,
  title: string,
  rest: Partial<HeldRequest> = {},
): HeldRequest {
  const written = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  return {
    id: `a1000000-0000-4000-8000-${String(number).padStart(12, '0')}`,
    workspace: workspace.id,
    number,
    title,
    status: 'open',
    body: '',
    createdBy: ada.id,
    createdAt: written,
    updatedAt: written,
    ...rest,
  };
}

/** A question an agent asked about a request an hour ago, for its person. */
export function question(
  of: HeldRequest,
  number: number,
  text: string,
  rest: Partial<HeldQuestion> = {},
): HeldQuestion {
  return {
    id: `a2000000-0000-4000-8000-${String(of.number * 100 + number).padStart(12, '0')}`,
    request: of.id,
    text,
    answer: null,
    askedBy: ada.id,
    askedByAgent: 'Claude Code',
    answeredBy: null,
    askedAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    answeredAt: null,
    ...rest,
  };
}

/** What the page asked of the stand-in. */
export interface RequestCalls {
  readonly rpc: { readonly name: string; readonly args: Record<string, unknown> }[];
  readonly patches: Record<string, unknown>[];
}

export async function standInRequests(
  page: Page,
  {
    requests = [],
    questions = [],
    specs = [],
  }: { requests?: HeldRequest[]; questions?: HeldQuestion[]; specs?: HeldSpec[] } = {},
): Promise<RequestCalls> {
  // Copies, so one test's changes don't reach the next.
  const held = {
    requests: requests.map((each) => ({ ...each })),
    questions: questions.map((each) => ({ ...each })),
  };
  const calls: RequestCalls = { rpc: [], patches: [] };
  const questionsOf = (id: string) => held.questions.filter((each) => each.request === id);
  const questionRow = (each: HeldQuestion) => ({
    id: each.id,
    text: each.text,
    answer: each.answer,
    asked_by: each.askedBy,
    asked_by_agent: each.askedByAgent,
    answered_by: each.answeredBy,
    asked_at: each.askedAt,
    answered_at: each.answeredAt,
  });

  await page.route(`${supabase}/rest/v1/requests**`, (route) => {
    const method = route.request().method();
    if (method === 'OPTIONS') return answer(route, 204);
    const url = new URL(route.request().url());
    if (method === 'PATCH') {
      const found = held.requests.find((each) => each.id === equal(url, 'id'));
      const body = route.request().postDataJSON() as Partial<HeldRequest>;
      calls.patches.push(body);
      if (found) Object.assign(found, body, { updatedAt: new Date().toISOString() });
      return answer(route, 204);
    }
    const workspace = equal(url, 'workspace_id');
    const number = equal(url, 'number');
    const rows = held.requests
      .filter((each) => each.workspace === workspace)
      .filter((each) => number === null || each.number === Number(number))
      .sort((a, b) => b.number - a.number)
      .map((each) => {
        const drafted = specs
          .filter((spec) => spec.request?.id === each.id)
          .map(({ number: n, title, status }) => ({ number: n, title, status }));
        return {
          id: each.id,
          number: each.number,
          title: each.title,
          status: each.status,
          body: each.body,
          created_by: each.createdBy,
          created_at: each.createdAt,
          updated_at: each.updatedAt,
          questions:
            number === null
              ? questionsOf(each.id).map(({ answer: given }) => ({ answer: given }))
              : questionsOf(each.id).map(questionRow),
          specs: number === null ? [{ count: drafted.length }] : drafted,
        };
      });
    return answer(route, 200, rows);
  });

  // The questions waiting on a person, on the open requests they wrote, as My work reads them.
  await page.route(`${supabase}/rest/v1/questions**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const writer = equal(new URL(route.request().url()), 'requests.created_by');
    const rows = held.questions.flatMap((each) => {
      const of = held.requests.find((one) => one.id === each.request);
      if (!of || of.createdBy !== writer || of.status !== 'open' || each.answer !== null) return [];
      return [
        {
          ...questionRow(each),
          requests: {
            number: of.number,
            title: of.title,
            status: of.status,
            created_by: of.createdBy,
          },
        },
      ];
    });
    return answer(route, 200, rows);
  });

  // Registered last, so it answers these functions before the workspace stand-in does.
  await page.route(/\/rest\/v1\/rpc\/(create_request|answer_question)/, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const name = new URL(route.request().url()).pathname.split('/').at(-1) ?? '';
    const args = route.request().postDataJSON() as Record<string, string>;
    calls.rpc.push({ name, args });
    if (name === 'answer_question') {
      const found = held.questions.find((each) => each.id === args.question);
      if (!found) return refuse(route, '42501', 'Only members can answer a question');
      Object.assign(found, {
        answer: args.answer,
        answeredBy: ada.id,
        answeredAt: new Date().toISOString(),
      });
      return answer(route, 204);
    }
    const workspace = String(args.workspace);
    const number =
      Math.max(
        0,
        ...held.requests.filter((each) => each.workspace === workspace).map((each) => each.number),
      ) + 1;
    held.requests.push(
      request({ id: workspace }, number, String(args.title), {
        id: crypto.randomUUID(),
        body: String(args.body ?? ''),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }),
    );
    return answer(route, 200, number);
  });

  return calls;
}
