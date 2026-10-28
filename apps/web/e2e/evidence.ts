import type { Page } from '@playwright/test';
import { supabase } from './supabase';
import { ada, answer, equal, refuse } from './workspaces';

// Stands in for a workspace's repositories, its CI reports and what they prove, as PostgREST
// answers them (decision record 50). Postgres works out each proof from the reports; here each
// criterion's proof is given, and confirming a reworded criterion's tests works it out again.

export interface HeldRepository {
  readonly id: string;
  readonly workspace: string;
  readonly name: string;
  branch: string;
}

export interface HeldReport {
  readonly id: string;
  readonly repository: string;
  readonly suite: string;
  readonly sha: string;
  readonly runId: number;
  readonly tests: number;
  readonly passed: number;
  readonly failed: number;
  readonly skipped: number;
}

export interface HeldProof {
  readonly criterion: string;
  readonly spec: { readonly id: string; readonly number: number; readonly title: string };
  readonly number: number;
  readonly text: string;
  passed: number;
  failed: number;
  skipped: number;
  suspectSince: string | null;
}

export interface HeldClaim {
  readonly spec: number;
  readonly criterion: number;
  readonly name: string;
  readonly outcome: 'passed' | 'failed' | 'skipped';
  readonly message?: string;
}

export interface Evidence {
  readonly repositories: HeldRepository[];
  readonly reports: HeldReport[];
  readonly proofs: HeldProof[];
  readonly claims: HeldClaim[];
}

export const sha = 'a1b2c3d4e5f60718293a4b5c6d7e8f9012345678';

/** One of the workspace's repositories, on its main branch. */
export function repository(workspace: { id: string }, name: string, number = 1): HeldRepository {
  return {
    id: `f0000000-0000-4000-8000-${String(number).padStart(12, '0')}`,
    workspace: workspace.id,
    name,
    branch: 'main',
  };
}

/** What the page asked of the stand-in. */
export interface EvidenceCalls {
  readonly rpc: { readonly name: string; readonly args: Record<string, unknown> }[];
  readonly patches: Record<string, unknown>[];
  readonly deleted: string[];
}

/** A criterion's proof, as criterion_proofs works it out from its tests. */
function stateOf(proof: HeldProof): 'proven' | 'failing' | 'unproven' {
  const tests = proof.passed + proof.failed + proof.skipped;
  if (proof.failed > 0) return 'failing';
  if (proof.suspectSince === null && tests > 0 && proof.passed === tests) return 'proven';
  return 'unproven';
}

/**
 * Stands in for the evidence tables and views, on top of standInTeam, whose empty answers for
 * them it takes over.
 */
export async function standInEvidence(
  page: Page,
  workspace: { id: string },
  { repositories = [], reports = [], proofs = [], claims = [] }: Partial<Evidence> = {},
): Promise<EvidenceCalls> {
  const held: Evidence = {
    repositories: repositories.map((each) => ({ ...each })),
    reports: reports.map((each) => ({ ...each })),
    proofs: proofs.map((each) => ({ ...each })),
    claims: [...claims],
  };
  const calls: EvidenceCalls = { rpc: [], patches: [], deleted: [] };
  const received = new Date(Date.now() - 5 * 60 * 1000).toISOString();

  await page.route(`${supabase}/rest/v1/repositories**`, (route) => {
    const method = route.request().method();
    if (method === 'OPTIONS') return answer(route, 204);
    const url = new URL(route.request().url());
    const at = held.repositories.findIndex((each) => each.id === equal(url, 'id'));
    if (method === 'PATCH') {
      const body = route.request().postDataJSON() as { branch: string };
      calls.patches.push(body);
      const found = held.repositories[at];
      if (found) found.branch = body.branch;
      return answer(route, 204);
    }
    if (method === 'DELETE') {
      const [gone] = held.repositories.splice(at, 1);
      if (gone) calls.deleted.push(gone.name);
      return answer(route, 204);
    }
    return answer(
      route,
      200,
      held.repositories
        .filter((each) => each.workspace === workspace.id)
        .map(({ id, name, branch }) => ({ id, name, branch, github_id: 101, added_at: received })),
    );
  });

  await page.route(`${supabase}/rest/v1/test_reports**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    return answer(
      route,
      200,
      held.reports
        .filter((report) => held.repositories.some((each) => each.name === report.repository))
        .map((report) => ({
          id: report.id,
          suite: report.suite,
          branch: 'main',
          sha: report.sha,
          run_id: report.runId,
          run_attempt: 1,
          workflow: 'CI',
          received_at: received,
          tests: report.tests,
          passed: report.passed,
          failed: report.failed,
          skipped: report.skipped,
          repositories: { name: report.repository },
        })),
    );
  });

  const proofRow = (proof: HeldProof) => ({
    criterion_id: proof.criterion,
    workspace_id: workspace.id,
    spec_id: proof.spec.id,
    spec_number: proof.spec.number,
    spec_title: proof.spec.title,
    spec_status: 'approved',
    criterion_number: proof.number,
    text: proof.text,
    suspect_since: proof.suspectSince,
    tests: proof.passed + proof.failed + proof.skipped,
    passed: proof.passed,
    failed: proof.failed,
    skipped: proof.skipped,
    state: stateOf(proof),
    checked_at: proof.passed + proof.failed + proof.skipped ? received : null,
    spec_owner_id: ada.id,
  });

  await page.route(`${supabase}/rest/v1/criterion_proofs**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const url = new URL(route.request().url());
    const specId = equal(url, 'spec_id');
    const state = equal(url, 'state');
    // Every spec the stand-in proves is Ada's.
    if (![null, ada.id].includes(equal(url, 'spec_owner_id'))) return answer(route, 200, []);
    return answer(
      route,
      200,
      held.proofs
        .filter((proof) => specId === null || proof.spec.id === specId)
        .filter((proof) => state === null || stateOf(proof) === state)
        .sort((a, b) => a.spec.number - b.spec.number || a.number - b.number)
        .map(proofRow),
    );
  });

  await page.route(`${supabase}/rest/v1/spec_proofs**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const specs = new Map<string, { criteria: number; proven: number; failing: number }>();
    for (const proof of held.proofs) {
      const counts = specs.get(proof.spec.id) ?? { criteria: 0, proven: 0, failing: 0 };
      const state = stateOf(proof);
      specs.set(proof.spec.id, {
        criteria: counts.criteria + 1,
        proven: counts.proven + (state === 'proven' ? 1 : 0),
        failing: counts.failing + (state === 'failing' ? 1 : 0),
      });
    }
    return answer(
      route,
      200,
      [...specs].map(([spec_id, counts]) => ({ spec_id, workspace_id: workspace.id, ...counts })),
    );
  });

  await page.route(`${supabase}/rest/v1/latest_claims**`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const number = Number(equal(new URL(route.request().url()), 'spec_number'));
    return answer(
      route,
      200,
      held.claims
        .filter((claim) => claim.spec === number)
        .map((claim, at) => ({
          id: at + 1,
          spec_number: claim.spec,
          criterion_number: claim.criterion,
          name: claim.name,
          classname: 'tests.test_pay',
          file: 'tests/test_pay.py',
          outcome: claim.outcome,
          message: claim.message ?? null,
          repository: held.repositories[0]?.name ?? 'acme-co/payments',
          suite: 'unit',
          sha,
          run_id: 1000,
          workflow: 'CI',
          received_at: received,
        })),
    );
  });

  // Registered last, so it answers these two functions before the workspace stand-in does.
  await page.route(/\/rest\/v1\/rpc\/(add_repository|confirm_criterion)/, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const name = new URL(route.request().url()).pathname.split('/').at(-1) ?? '';
    const args = route.request().postDataJSON() as Record<string, string>;
    calls.rpc.push({ name, args });
    if (name === 'confirm_criterion') {
      const proof = held.proofs.find((each) => each.criterion === args.criterion);
      if (proof) proof.suspectSince = null;
      return answer(route, 204);
    }
    const added = String(args.name);
    if (held.repositories.some((each) => each.name.toLowerCase() === added.toLowerCase())) {
      return refuse(route, '23505', 'This workspace already has that repository');
    }
    const made = {
      id: crypto.randomUUID(),
      workspace: workspace.id,
      name: added,
      branch: String(args.branch),
    };
    held.repositories.push(made);
    return answer(route, 200, made.id);
  });

  return calls;
}
