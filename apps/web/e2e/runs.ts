import type { Page } from '@playwright/test';
import { supabase } from './supabase';
import { ada, answer, equal } from './workspaces';

// Stands in for the runs of Sulba's agents on a request, as PostgREST answers them, and for the
// Worker's routes that start and check one (decision record 64), so no test reaches Anthropic.
// Call it after standInSpecs, whose empty runs it takes over.

export interface HeldRun {
  readonly id: string;
  readonly request: string;
  status: 'running' | 'done' | 'failed' | 'stopped';
  readonly budgetCents: number;
  costCents: number;
  note: string | null;
  readonly startedBy: string | null;
  readonly startedAt: string;
  endedAt: string | null;
}

export interface RunCalls {
  /** What the page sent to start a run, the token it sent it with, and the run it got. */
  readonly started: {
    readonly body: unknown;
    readonly authorization: string | null;
    readonly run: string | null;
  }[];
  /** Ends a running run, as the Worker would once its agent finishes. */
  readonly finish: (run: string, ending: { costCents: number; note: string }) => void;
}

/**
 * Stands in for runs, the month's spending against a limit in US cents, and the Worker's start
 * route, which starts a run by Ada with a $1.00 budget unless `refusal` says why it can't.
 */
export async function standInRuns(
  page: Page,
  {
    runs = [],
    limitCents = 250,
    refusal,
  }: { runs?: HeldRun[]; limitCents?: number; refusal?: string } = {},
): Promise<RunCalls> {
  const held = runs.map((each) => ({ ...each }));
  const calls: RunCalls = {
    started: [],
    finish: (run, ending) => {
      const found = held.find((each) => each.id === run);
      if (!found) return;
      Object.assign(found, {
        status: 'done',
        costCents: ending.costCents,
        note: ending.note,
        endedAt: new Date().toISOString(),
      });
    },
  };

  await page.route(`${supabase}/rest/v1/agent_runs**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const request = equal(new URL(route.request().url()), 'request_id');
    const rows = held
      .filter((each) => each.request === request)
      .sort((a, b) => b.startedAt.localeCompare(a.startedAt))
      .map((each) => ({
        id: each.id,
        role: 'intake',
        status: each.status,
        budget_cents: each.budgetCents,
        cost_cents: each.costCents,
        note: each.note,
        started_by: each.startedBy,
        started_at: each.startedAt,
        ended_at: each.endedAt,
      }));
    return answer(route, 200, rows);
  });

  await page.route(/\/rest\/v1\/rpc\/agent_spending/, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const spent = held
      .filter((each) => each.status !== 'running')
      .reduce((sum, each) => sum + each.costCents, 0);
    const reserved = held
      .filter((each) => each.status === 'running')
      .reduce((sum, each) => sum + each.budgetCents, 0);
    return answer(route, 200, [
      { limit_cents: limitCents, spent_cents: spent, reserved_cents: reserved },
    ]);
  });

  await page.route('**/api/agents/runs', (route) => {
    const body = route.request().postDataJSON() as { request: string };
    const authorization = route.request().headers().authorization ?? null;
    if (refusal) {
      calls.started.push({ body, authorization, run: null });
      return route.fulfill({ status: 409, json: { message: refusal } });
    }
    const id = crypto.randomUUID();
    calls.started.push({ body, authorization, run: id });
    held.push({
      id,
      request: body.request,
      status: 'running',
      budgetCents: 100,
      costCents: 0,
      note: null,
      startedBy: ada.id,
      startedAt: new Date().toISOString(),
      endedAt: null,
    });
    return route.fulfill({ status: 201, json: { run: id } });
  });

  await page.route('**/api/agents/check', (route) => route.fulfill({ status: 204 }));

  return calls;
}
