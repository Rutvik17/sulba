import type { Page } from '@playwright/test';
import { supabase } from './supabase';
import { ada, answer, equal, refuse } from './workspaces';

// Stands in for the specs and criteria tables, their reviews, their functions and their history,
// as PostgREST answers them (decisions 49 and 52). Each change the page makes is logged as the
// trigger would, and a change to a spec in review asks its approvers again, as Postgres does.

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

export type Verdict = 'pending' | 'approved' | 'changes_requested';

export interface HeldReview {
  readonly id: string;
  readonly spec: string;
  readonly reviewer: string;
  requestedBy: string;
  requestedAt: string;
  verdict: Verdict;
  note: string | null;
  answeredAt: string | null;
}

export interface Writing {
  readonly specs: HeldSpec[];
  readonly criteria: HeldCriterion[];
  readonly reviews: HeldReview[];
}

/** A review of a spec, asked for an hour ago by Ada. */
export function review(
  of: HeldSpec,
  reviewer: { id: string },
  rest: Partial<HeldReview> = {},
): HeldReview {
  return {
    id: `f1000000-0000-4000-8000-${String(of.number).padStart(6, '0')}${reviewer.id.slice(-6)}`,
    spec: of.id,
    reviewer: reviewer.id,
    requestedBy: ada.id,
    requestedAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    verdict: 'pending',
    note: null,
    answeredAt: null,
    ...rest,
  };
}

/** The values of a PostgREST filter such as `status=in.(draft,in_review)`. */
function within(url: URL, column: string): string[] | null {
  const filter = url.searchParams.get(column);
  return filter?.startsWith('in.(') ? filter.slice(4, -1).split(',') : null;
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
  { specs = [], criteria = [], reviews = [] }: Partial<Writing> = {},
): Promise<WritingCalls> {
  // Copies, so one test's changes don't reach the next.
  const held: Writing = {
    specs: specs.map((each) => ({ ...each })),
    criteria: criteria.map((each) => ({ ...each })),
    reviews: reviews.map((each) => ({ ...each })),
  };
  const events: HeldEvent[] = [];
  const calls: WritingCalls = { rpc: [], patches: [] };
  const lastCriterion = new Map<string, number>();
  for (const each of held.criteria) {
    lastCriterion.set(each.spec, Math.max(lastCriterion.get(each.spec) ?? 0, each.number));
  }
  const log = (event: Omit<HeldEvent, 'id'>) => events.push({ id: events.length + 1, ...event });
  const reviewsOf = (id: string) => held.reviews.filter((each) => each.spec === id);
  // A change to a spec in review asks those who approved it to review it again.
  const askAgain = (id: string) => {
    if (held.specs.find((each) => each.id === id)?.status !== 'in_review') return;
    for (const each of reviewsOf(id)) {
      if (each.verdict !== 'approved') continue;
      Object.assign(each, { verdict: 'pending', note: null, answeredAt: null });
      log({
        spec: id,
        action: 'review.updated',
        subjectType: 'review',
        subjectId: each.id,
        changes: { verdict: ['approved', 'pending'] },
      });
    }
  };
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
      if (
        found &&
        body.status === 'approved' &&
        reviewsOf(found.id).some((each) => each.verdict !== 'approved')
      ) {
        return refuse(route, '23514', 'Every reviewer has to approve the spec first');
      }
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
        if ('title' in body || 'body' in body) askAgain(found.id);
      }
      return answer(route, 204);
    }
    const workspace = equal(url, 'workspace_id');
    const number = equal(url, 'number');
    const owner = equal(url, 'owner_id');
    const statuses = within(url, 'status');
    const rows = held.specs
      .filter((each) => each.workspace === workspace)
      .filter((each) => number === null || each.number === Number(number))
      .filter((each) => owner === null || each.ownerId === owner)
      .filter((each) => statuses === null || statuses.includes(each.status))
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
        spec_reviews: reviewsOf(each.id).map(({ verdict }) => ({ verdict })),
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
      askAgain(found.spec);
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
      askAgain(found.spec);
    }
    return answer(route, 204);
  });

  await page.route(`${supabase}/rest/v1/spec_reviews**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const url = new URL(route.request().url());
    const specId = equal(url, 'spec_id');
    const row = (each: HeldReview) => ({
      id: each.id,
      spec_id: each.spec,
      reviewer_id: each.reviewer,
      requested_by: each.requestedBy,
      requested_at: each.requestedAt,
      verdict: each.verdict,
      note: each.note,
      answered_at: each.answeredAt,
    });
    if (specId !== null) return answer(route, 200, reviewsOf(specId).map(row));
    // The reviews asked of a person, with their specs in review, as My work reads them.
    const reviewer = equal(url, 'reviewer_id');
    const verdicts = within(url, 'verdict') ?? [];
    const rows = held.reviews
      .filter((each) => each.reviewer === reviewer && verdicts.includes(each.verdict))
      .flatMap((each) => {
        const of = held.specs.find((one) => one.id === each.spec);
        if (of?.status !== 'in_review') return [];
        return [
          {
            ...row(each),
            specs: {
              id: of.id,
              number: of.number,
              title: of.title,
              status: of.status,
              owner_id: of.ownerId,
              updated_at: of.updatedAt,
            },
          },
        ];
      });
    return answer(route, 200, rows);
  });

  // The criteria's proofs, which the evidence stand-in answers when a test holds any.
  await page.route(`${supabase}/rest/v1/criterion_proofs**`, (route) =>
    route.request().method() === 'OPTIONS' ? answer(route, 204) : answer(route, 200, []),
  );

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
      askAgain(String(args.spec));
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

  await page.route(/\/rest\/v1\/rpc\/(request_review|remove_reviewer|review_spec)/, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const name = new URL(route.request().url()).pathname.split('/').at(-1) ?? '';
    const args = route.request().postDataJSON() as Record<string, string>;
    calls.rpc.push({ name, args });
    const of = held.specs.find((each) => each.id === args.spec);
    if (!of) return refuse(route, '42501', 'Only members can choose a spec’s reviewers');
    const now = new Date().toISOString();
    if (name === 'request_review') {
      if (args.reviewer === of.ownerId) {
        return refuse(route, '23514', 'A spec’s owner doesn’t review it');
      }
      const found = reviewsOf(of.id).find((each) => each.reviewer === args.reviewer);
      if (found) {
        const before = found.verdict;
        Object.assign(found, {
          verdict: 'pending',
          note: null,
          answeredAt: null,
          requestedAt: now,
        });
        log({
          spec: of.id,
          action: 'review.updated',
          subjectType: 'review',
          subjectId: found.id,
          changes: { verdict: [before, 'pending'] },
        });
      } else {
        const made = review(of, { id: String(args.reviewer) }, { requestedAt: now });
        held.reviews.push(made);
        log({
          spec: of.id,
          action: 'review.created',
          subjectType: 'review',
          subjectId: made.id,
          changes: { reviewer_id: [null, made.reviewer], verdict: [null, 'pending'] },
        });
      }
      return answer(route, 204);
    }
    if (name === 'remove_reviewer') {
      const at = held.reviews.findIndex(
        (each) => each.spec === of.id && each.reviewer === args.reviewer,
      );
      const [gone] = held.reviews.splice(at, 1);
      if (gone) {
        log({
          spec: of.id,
          action: 'review.deleted',
          subjectType: 'review',
          subjectId: gone.id,
          changes: { reviewer_id: [gone.reviewer, null] },
        });
      }
      return answer(route, 204);
    }
    const yours = reviewsOf(of.id).find((each) => each.reviewer === ada.id);
    if (!yours) return refuse(route, '42501', 'Only the spec’s reviewers can review it');
    if (args.verdict === 'changes_requested' && !args.note) {
      return refuse(route, '23514', 'Say what to change');
    }
    const before = yours.verdict;
    Object.assign(yours, {
      verdict: args.verdict as Verdict,
      note: args.note ?? null,
      answeredAt: now,
    });
    log({
      spec: of.id,
      action: 'review.updated',
      subjectType: 'review',
      subjectId: yours.id,
      changes: { verdict: [before, args.verdict] },
    });
    if (reviewsOf(of.id).every((each) => each.verdict === 'approved')) {
      log({
        spec: of.id,
        action: 'spec.updated',
        subjectType: 'spec',
        subjectId: of.id,
        changes: { status: [of.status, 'approved'] },
      });
      of.status = 'approved';
      of.updatedAt = now;
    }
    return answer(route, 200, of.status);
  });

  return calls;
}
