import type { Page } from '@playwright/test';
import { supabase } from './supabase';
import { ada, answer, equal } from './workspaces';

// Stands in for a request's releases and approve_release, as PostgREST answers them (decision
// record 62). Call it after standInSpecs, whose empty release list it takes over.

/** What an approved release keeps of each spec, as Postgres writes it. */
export interface HeldSnapshotSpec {
  readonly number: number;
  readonly title: string;
  readonly status: string;
  readonly criteria: readonly { number: number; text: string; tests: number }[];
  readonly tasks: readonly {
    number: number;
    title: string;
    role: string;
    status: string;
    pull_request: string | null;
  }[];
}

export interface HeldRelease {
  readonly id: string;
  readonly request: string;
  readonly number: number;
  readonly note: string | null;
  readonly approvedBy: string | null;
  readonly approvedAt: string;
  readonly snapshot: readonly HeldSnapshotSpec[];
}

/** What the page asked of the stand-in. */
export interface ReleaseCalls {
  readonly rpc: { readonly name: string; readonly args: Record<string, unknown> }[];
}

/**
 * Stands in for releases. An approval adds a release by Ada that keeps `snapshot`, as Postgres
 * would once the request is ready.
 */
export async function standInReleases(
  page: Page,
  {
    releases = [],
    snapshot = [],
  }: { releases?: HeldRelease[]; snapshot?: readonly HeldSnapshotSpec[] } = {},
): Promise<ReleaseCalls> {
  const held = [...releases];
  const calls: ReleaseCalls = { rpc: [] };

  await page.route(`${supabase}/rest/v1/releases**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const request = equal(new URL(route.request().url()), 'request_id');
    const rows = held
      .filter((each) => each.request === request)
      .sort((a, b) => b.number - a.number)
      .map((each) => ({
        id: each.id,
        number: each.number,
        note: each.note,
        approved_by: each.approvedBy,
        approved_at: each.approvedAt,
        snapshot: each.snapshot,
      }));
    return answer(route, 200, rows);
  });

  await page.route(/\/rest\/v1\/rpc\/approve_release/, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const args = route.request().postDataJSON() as Record<string, string>;
    calls.rpc.push({ name: 'approve_release', args });
    const number = held.filter((each) => each.request === args.request).length + 1;
    held.push({
      id: crypto.randomUUID(),
      request: String(args.request),
      number,
      note: args.note ?? null,
      approvedBy: ada.id,
      approvedAt: new Date().toISOString(),
      snapshot,
    });
    return answer(route, 200, number);
  });

  return calls;
}
