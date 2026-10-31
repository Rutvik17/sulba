import type { Page } from '@playwright/test';
import type { HeldCriterion, HeldSpec } from './specs';
import { supabase } from './supabase';
import { ada, answer, equal, refuse } from './workspaces';

// Stands in for tasks and their functions, as PostgREST answers them (decision record 61). Call it
// after standInSpecs, whose empty task list it takes over.

export type TaskStatus = 'open' | 'in_progress' | 'blocked' | 'in_review' | 'done' | 'canceled';

export interface HeldTask {
  readonly id: string;
  readonly spec: HeldSpec;
  readonly number: number;
  title: string;
  role: 'build' | 'test' | 'review' | 'document';
  status: TaskStatus;
  body: string;
  note: string | null;
  takenBy: string | null;
  takenByAgent: string | null;
  pullRequest: string | null;
  /** The numbers of the spec's criteria it covers. */
  readonly criteria: readonly number[];
  readonly createdAt: string;
  updatedAt: string;
}

/** An open task of the spec's, written an hour ago by Ada's agent. */
export function task(
  of: HeldSpec,
  number: number,
  title: string,
  rest: Partial<HeldTask> = {},
): HeldTask {
  const written = new Date(Date.now() - 60 * 60 * 1000).toISOString();
  return {
    id: `a3000000-0000-4000-8000-${String(number).padStart(12, '0')}`,
    spec: of,
    number,
    title,
    role: 'build',
    status: 'open',
    body: '',
    note: null,
    takenBy: null,
    takenByAgent: null,
    pullRequest: null,
    criteria: [],
    createdAt: written,
    updatedAt: written,
    ...rest,
  };
}

/** What the page asked of the stand-in. */
export interface TaskCalls {
  readonly rpc: { readonly name: string; readonly args: Record<string, unknown> }[];
  readonly patches: Record<string, unknown>[];
}

export async function standInTasks(
  page: Page,
  {
    tasks = [],
    specs = [],
    criteria = [],
  }: { tasks?: HeldTask[]; specs?: HeldSpec[]; criteria?: HeldCriterion[] } = {},
): Promise<TaskCalls> {
  // Copies, so one test's changes don't reach the next.
  const held = tasks.map((each) => ({ ...each }));
  const calls: TaskCalls = { rpc: [], patches: [] };
  const row = (each: HeldTask) => ({
    id: each.id,
    number: each.number,
    title: each.title,
    role: each.role,
    status: each.status,
    body: each.body,
    note: each.note,
    taken_by: each.takenBy,
    taken_by_agent: each.takenByAgent,
    taken_at: each.takenBy || each.takenByAgent ? each.updatedAt : null,
    pull_request: each.pullRequest,
    created_by: ada.id,
    created_by_agent: 'Claude Code',
    created_at: each.createdAt,
    updated_at: each.updatedAt,
    specs: {
      id: each.spec.id,
      number: each.spec.number,
      title: each.spec.title,
      status: each.spec.status,
      owner_id: each.spec.ownerId,
    },
    task_criteria: criteria
      .filter((one) => one.spec === each.spec.id && each.criteria.includes(one.number))
      .map(({ number, text }) => ({ criteria: { number, text } })),
  });

  await page.route(`${supabase}/rest/v1/tasks**`, (route) => {
    const method = route.request().method();
    if (method === 'OPTIONS') return answer(route, 204);
    const url = new URL(route.request().url());
    if (method === 'PATCH') {
      const found = held.find((each) => each.id === equal(url, 'id'));
      const body = route.request().postDataJSON() as Partial<HeldTask>;
      calls.patches.push(body);
      if (found) Object.assign(found, body, { updatedAt: new Date().toISOString() });
      return answer(route, 204);
    }
    const workspace = equal(url, 'workspace_id');
    const spec = equal(url, 'spec_id');
    const number = equal(url, 'number');
    const statuses = url.searchParams
      .get('status')
      ?.match(/^in\.\((.*)\)$/)?.[1]
      ?.split(',');
    const owner = equal(url, 'specs.owner_id');
    const rows = held
      .filter((each) => workspace === null || each.spec.workspace === workspace)
      .filter((each) => spec === null || each.spec.id === spec)
      .filter((each) => number === null || each.number === Number(number))
      .filter((each) => !statuses || statuses.includes(each.status))
      .filter((each) => owner === null || each.spec.ownerId === owner)
      .sort((a, b) => (spec === null ? b.number - a.number : a.number - b.number))
      .map(row);
    return answer(route, 200, rows);
  });

  // Registered last, so it answers these functions before the workspace stand-in does.
  await page.route(/\/rest\/v1\/rpc\/(create_task|update_task)/, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const name = new URL(route.request().url()).pathname.split('/').at(-1) ?? '';
    const args = route.request().postDataJSON() as Record<string, string>;
    calls.rpc.push({ name, args });
    if (name === 'update_task') {
      const found = held.find((each) => each.id === args.task);
      if (!found) return refuse(route, '42501', 'Only members can work on tasks');
      const status = args.status as TaskStatus;
      Object.assign(found, {
        status,
        note: status === 'in_progress' || status === 'open' ? null : (args.note ?? found.note),
        pullRequest: args.pull_request ?? found.pullRequest,
        updatedAt: new Date().toISOString(),
        ...(found.status === 'open' && status === 'in_progress'
          ? { takenBy: ada.id, takenByAgent: null }
          : {}),
        ...(status === 'open' ? { takenBy: null, takenByAgent: null } : {}),
      });
      return answer(route, 204);
    }
    const of = specs.find((each) => each.id === args.spec);
    if (!of) return refuse(route, '42501', 'Only members can write tasks');
    const number =
      Math.max(
        0,
        ...held.filter((each) => each.spec.workspace === of.workspace).map((each) => each.number),
      ) + 1;
    held.push(
      task(of, number, String(args.title), {
        id: crypto.randomUUID(),
        role: args.role as HeldTask['role'],
        body: String(args.body ?? ''),
        criteria: (args.criteria as unknown as number[] | undefined) ?? [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }),
    );
    return answer(route, 200, number);
  });

  return calls;
}
