import type { Page } from '@playwright/test';
import { supabase } from './supabase';
import { ada, answer, equal } from './workspaces';

// Stands in for the specs and criteria tables, their functions and their history, as PostgREST
// answers them (decision record 49). Each change the page makes is logged as the trigger would.

export type SpecStatus =
  | 'draft'
  | 'in_review'
  | 'approved'
  | 'implemented'
  | 'abandoned'
  | 'superseded';

export interface HeldSpec {
  readonly id: string;
  readonly workspace: string;
  readonly number: number;
  title: string;
  status: SpecStatus;
  body: string;
  ownerId: string | null;
  readonly createdAt: string;
  updatedAt: string;
}

export interface HeldCriterion {
  readonly id: string;
  readonly spec: string;
  readonly number: number;
  text: string;
}

interface HeldEvent {
  readonly id: number;
  readonly spec: string;
  readonly action: string;
  readonly subjectType: string;
  readonly subjectId: string;
  readonly changes: Record<string, unknown>;
}

export interface Writing {
  readonly specs: HeldSpec[];
  readonly criteria: HeldCriterion[];
}

/** A spec of the workspace's, written a day ago by Ada, who owns it. */
export function spec(
  workspace: { id: string },
  number: number,
  title: string,
  rest: Partial<HeldSpec> = {},
): HeldSpec {
  const written = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  return {
    id: `d0000000-0000-4000-8000-${String(number).padStart(12, '0')}`,
    workspace: workspace.id,
    number,
    title,
    status: 'draft',
    body: '',
    ownerId: ada.id,
    createdAt: written,
    updatedAt: written,
    ...rest,
  };
}

export function criterion(of: HeldSpec, number: number, text: string): HeldCriterion {
  return {
    id: `e0000000-0000-4000-8000-${String(of.number * 100 + number).padStart(12, '0')}`,
    spec: of.id,
    number,
    text,
  };
}

/** What the page asked of the stand-in. */
export interface WritingCalls {
  readonly rpc: { readonly name: string; readonly args: Record<string, unknown> }[];
  readonly patches: { readonly table: string; readonly body: Record<string, unknown> }[];
}

/**
 * Stands in for specs, criteria and their history. Call it after standInTeam, whose function
 * route it takes over for create_spec and add_criterion.
 */
export async function standInSpecs(
  page: Page,
  { specs = [], criteria = [] }: Partial<Writing> = {},
): Promise<WritingCalls> {
  // Copies, so one test's changes don't reach the next.
  const held: Writing = {
    specs: specs.map((each) => ({ ...each })),
    criteria: criteria.map((each) => ({ ...each })),
  };
  const events: HeldEvent[] = [];
  const calls: WritingCalls = { rpc: [], patches: [] };
  const lastCriterion = new Map<string, number>();
  for (const each of held.criteria) {
    lastCriterion.set(each.spec, Math.max(lastCriterion.get(each.spec) ?? 0, each.number));
  }
  const log = (event: Omit<HeldEvent, 'id'>) => events.push({ id: events.length + 1, ...event });
  const criteriaOf = (id: string) =>
    held.criteria
      .filter((each) => each.spec === id)
      .sort((a, b) => a.number - b.number)
      .map(({ id: criterionId, number, text }) => ({ id: criterionId, number, text }));

  await page.route(`${supabase}/rest/v1/specs**`, (route) => {
    const method = route.request().method();
    if (method === 'OPTIONS') return answer(route, 204);
    const url = new URL(route.request().url());
    if (method === 'PATCH') {
      const found = held.specs.find((each) => each.id === equal(url, 'id'));
      const body = route.request().postDataJSON() as Record<string, unknown>;
      calls.patches.push({ table: 'specs', body });
      if (found) {
        const changes: Record<string, unknown> = {};
        for (const [field, value] of Object.entries(body)) {
          const name = field === 'owner_id' ? 'ownerId' : field;
          const before = found[name as keyof HeldSpec];
          changes[field] = field === 'body' ? null : [before, value];
          Object.assign(found, { [name]: value });
        }
        found.updatedAt = new Date().toISOString();
        log({
          spec: found.id,
          action: 'spec.updated',
          subjectType: 'spec',
          subjectId: found.id,
          changes,
        });
      }
      return answer(route, 204);
    }
    const workspace = equal(url, 'workspace_id');
    const number = equal(url, 'number');
    const rows = held.specs
      .filter((each) => each.workspace === workspace)
      .filter((each) => number === null || each.number === Number(number))
      .sort((a, b) => b.number - a.number)
      .map((each) => ({
        id: each.id,
        number: each.number,
        title: each.title,
        status: each.status,
        body: each.body,
        owner_id: each.ownerId,
        created_at: each.createdAt,
        updated_at: each.updatedAt,
        criteria: number === null ? [{ count: criteriaOf(each.id).length }] : criteriaOf(each.id),
      }));
    return answer(route, 200, rows);
  });

  await page.route(`${supabase}/rest/v1/criteria**`, (route) => {
    const method = route.request().method();
    if (method === 'OPTIONS') return answer(route, 204);
    const url = new URL(route.request().url());
    const at = held.criteria.findIndex((each) => each.id === equal(url, 'id'));
    const found = held.criteria[at];
    if (found && method === 'DELETE') {
      held.criteria.splice(at, 1);
      log({
        spec: found.spec,
        action: 'criterion.deleted',
        subjectType: 'criterion',
        subjectId: found.id,
        changes: { number: [found.number, null], text: [found.text, null] },
      });
    }
    if (found && method === 'PATCH') {
      const { text } = route.request().postDataJSON() as { text: string };
      calls.patches.push({ table: 'criteria', body: { text } });
      log({
        spec: found.spec,
        action: 'criterion.updated',
        subjectType: 'criterion',
        subjectId: found.id,
        changes: { text: [found.text, text] },
      });
      found.text = text;
    }
    return answer(route, 204);
  });

  await page.route(`${supabase}/rest/v1/events**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const specId = equal(new URL(route.request().url()), 'spec_id');
    const rows = events
      .filter((each) => each.spec === specId)
      .reverse()
      .map((each) => ({
        id: each.id,
        at: new Date().toISOString(),
        actor_kind: 'person',
        action: each.action,
        subject_type: each.subjectType,
        subject_id: each.subjectId,
        changes: each.changes,
        people: { name: ada.name },
      }));
    return answer(route, 200, rows);
  });

  // Registered last, so it answers these two functions before the workspace stand-in does.
  await page.route(/\/rest\/v1\/rpc\/(create_spec|add_criterion)/, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const name = new URL(route.request().url()).pathname.split('/').at(-1) ?? '';
    const args = route.request().postDataJSON() as Record<string, unknown>;
    calls.rpc.push({ name, args });
    const add = (specId: string, text: string) => {
      const number = (lastCriterion.get(specId) ?? 0) + 1;
      lastCriterion.set(specId, number);
      const made = { id: crypto.randomUUID(), spec: specId, number, text };
      held.criteria.push(made);
      log({
        spec: specId,
        action: 'criterion.created',
        subjectType: 'criterion',
        subjectId: made.id,
        changes: { number: [null, number], text: [null, text] },
      });
      return number;
    };
    if (name === 'add_criterion') {
      return answer(route, 200, add(String(args.spec), String(args.text)));
    }
    const workspace = String(args.workspace);
    const number =
      Math.max(
        0,
        ...held.specs.filter((each) => each.workspace === workspace).map((each) => each.number),
      ) + 1;
    const made = spec({ id: workspace }, number, String(args.title), {
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
    held.specs.push(made);
    log({
      spec: made.id,
      action: 'spec.created',
      subjectType: 'spec',
      subjectId: made.id,
      changes: {},
    });
    for (const text of (args.criteria as string[] | undefined) ?? []) add(made.id, text);
    return answer(route, 200, number);
  });

  return calls;
}
