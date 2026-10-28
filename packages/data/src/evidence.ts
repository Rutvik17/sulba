// What a workspace's CI shows about its criteria (decision record 50): the GitHub repositories it
// takes test reports from, the reports themselves, the tests that name each criterion, and each
// criterion's proof.
import type { Client } from './client.ts';
import type { Database } from './database.ts';
import { refusal } from './refusal.ts';

export type Proof = Database['public']['Enums']['proof'];
export type SpecStatus = Database['public']['Enums']['spec_status'];
export type Outcome = Database['public']['Enums']['test_outcome'];

export const proofNames: Record<Proof, string> = {
  proven: 'Proven',
  failing: 'Failing',
  unproven: 'Unproven',
};

export interface Repository {
  readonly id: string;
  /** owner/name. */
  readonly name: string;
  /** The branch whose runs prove criteria. */
  readonly branch: string;
  /** GitHub's ID for it, known once it has sent a report. */
  readonly githubId: number | null;
  readonly addedAt: string;
}

/** One report from one run of a workflow. */
export interface Report {
  readonly id: string;
  readonly repository: string;
  readonly suite: string;
  readonly branch: string;
  readonly sha: string;
  readonly runId: number;
  readonly runAttempt: number;
  readonly workflow: string;
  readonly receivedAt: string;
  readonly tests: number;
  readonly passed: number;
  readonly failed: number;
  readonly skipped: number;
}

export interface CriterionProof {
  readonly criterionId: string;
  readonly specId: string;
  readonly specNumber: number;
  readonly specTitle: string;
  readonly specStatus: SpecStatus;
  readonly criterionNumber: number;
  readonly text: string;
  readonly state: Proof;
  /** How many tests name it in the latest reports, and how each ended. */
  readonly tests: number;
  readonly passed: number;
  readonly failed: number;
  readonly skipped: number;
  /** When it was reworded while tests named it, until a member confirms its tests. */
  readonly suspectSince: string | null;
  /** When the latest report that names it arrived. */
  readonly checkedAt: string | null;
}

export interface SpecProof {
  readonly criteria: number;
  readonly proven: number;
  readonly failing: number;
}

/** A test in a latest report that names a criterion, with the run it comes from. */
export interface Claim {
  readonly id: number;
  readonly specNumber: number;
  readonly criterionNumber: number;
  readonly name: string;
  readonly classname: string;
  readonly file: string | null;
  readonly outcome: Outcome;
  /** What the failure said. */
  readonly message: string | null;
  readonly repository: string;
  readonly suite: string;
  readonly sha: string;
  readonly runId: number;
  readonly workflow: string;
  readonly receivedAt: string;
}

/** What's wrong with a repository's name, or null. */
export function repositoryProblem(name: string): string | null {
  const trimmed = name.trim();
  if (trimmed === '') return 'Name the repository as owner/name.';
  const [owner, repository, ...rest] = trimmed.split('/');
  const valid =
    rest.length === 0 &&
    /^[A-Za-z0-9-]{1,100}$/.test(owner ?? '') &&
    /^[A-Za-z0-9_.-]{1,100}$/.test(repository ?? '') &&
    repository !== '.' &&
    repository !== '..';
  return valid ? null : 'Write it as owner/name, as GitHub shows it, such as acme/payments.';
}

/** What's wrong with a branch's name, or null. */
export function branchProblem(branch: string): string | null {
  const trimmed = branch.trim();
  if (trimmed === '') return 'Name the branch, such as main.';
  if (!/^\S{1,255}$/.test(trimmed)) return 'A branch’s name has no spaces.';
  return null;
}

export async function repositoriesOf(client: Client, workspaceId: string): Promise<Repository[]> {
  const { data, error } = await client
    .from('repositories')
    .select('id, name, branch, github_id, added_at')
    .eq('workspace_id', workspaceId)
    .order('name');
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    name: row.name,
    branch: row.branch,
    githubId: row.github_id,
    addedAt: row.added_at,
  }));
}

export async function addRepository(
  client: Client,
  workspaceId: string,
  name: string,
  branch: string,
): Promise<string> {
  const { data, error } = await client.rpc('add_repository', {
    workspace: workspaceId,
    name: name.trim(),
    branch: branch.trim(),
  });
  if (error) throw refusal(error, 'This workspace already has that repository.');
  return data;
}

export async function setBranch(client: Client, id: string, branch: string): Promise<void> {
  const { error } = await client
    .from('repositories')
    .update({ branch: branch.trim() })
    .eq('id', id);
  if (error) throw refusal(error);
}

/** Removes a repository, with its reports and what they proved. */
export async function removeRepository(client: Client, id: string): Promise<void> {
  const { error } = await client.from('repositories').delete().eq('id', id);
  if (error) throw refusal(error);
}

/** The workspace's latest reports, newest first: the last 20. */
export async function reportsOf(client: Client, workspaceId: string): Promise<Report[]> {
  const { data, error } = await client
    .from('test_reports')
    .select(
      'id, suite, branch, sha, run_id, run_attempt, workflow, received_at, tests, passed, failed, skipped, repositories(name)',
    )
    .eq('workspace_id', workspaceId)
    .order('received_at', { ascending: false })
    .limit(20);
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    repository: row.repositories.name,
    suite: row.suite,
    branch: row.branch,
    sha: row.sha,
    runId: row.run_id,
    runAttempt: row.run_attempt,
    workflow: row.workflow,
    receivedAt: row.received_at,
    tests: row.tests,
    passed: row.passed,
    failed: row.failed,
    skipped: row.skipped,
  }));
}

type ProofRow = Database['public']['Views']['criterion_proofs']['Row'];

function proofOf(row: ProofRow): CriterionProof {
  return {
    criterionId: row.criterion_id,
    specId: row.spec_id,
    specNumber: row.spec_number,
    specTitle: row.spec_title,
    specStatus: row.spec_status,
    criterionNumber: row.criterion_number,
    text: row.text,
    state: row.state ?? 'unproven',
    tests: row.tests ?? 0,
    passed: row.passed ?? 0,
    failed: row.failed ?? 0,
    skipped: row.skipped ?? 0,
    suspectSince: row.suspect_since,
    checkedAt: row.checked_at,
  };
}

/** Every criterion's proof in the workspace, by spec and criterion. */
export async function proofsOf(client: Client, workspaceId: string): Promise<CriterionProof[]> {
  const { data, error } = await client
    .from('criterion_proofs')
    .select('*')
    .eq('workspace_id', workspaceId)
    .order('spec_number')
    .order('criterion_number');
  if (error) throw refusal(error);
  return data.map(proofOf);
}

/** The criteria failing on a person's specs, most recently checked first: at most 50. */
export async function failingOn(
  client: Client,
  workspaceId: string,
  ownerId: string,
): Promise<CriterionProof[]> {
  const { data, error } = await client
    .from('criterion_proofs')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('spec_owner_id', ownerId)
    .eq('state', 'failing')
    .order('checked_at', { ascending: false })
    .limit(50);
  if (error) throw refusal(error);
  return data.map(proofOf);
}

/** The proofs of one spec's criteria. */
export async function proofsOfSpec(
  client: Client,
  workspaceId: string,
  specId: string,
): Promise<CriterionProof[]> {
  const { data, error } = await client
    .from('criterion_proofs')
    .select('*')
    .eq('workspace_id', workspaceId)
    .eq('spec_id', specId)
    .order('criterion_number');
  if (error) throw refusal(error);
  return data.map(proofOf);
}

/** How many of each spec's criteria are proven and failing, by the spec's ID. */
export async function specProofsOf(
  client: Client,
  workspaceId: string,
): Promise<Map<string, SpecProof>> {
  const { data, error } = await client
    .from('spec_proofs')
    .select('spec_id, criteria, proven, failing')
    .eq('workspace_id', workspaceId);
  if (error) throw refusal(error);
  return new Map(
    data.map((row) => [
      row.spec_id,
      { criteria: row.criteria ?? 0, proven: row.proven ?? 0, failing: row.failing ?? 0 },
    ]),
  );
}

/** The tests in the latest reports that name one of a spec's criteria. */
export async function claimsOfSpec(
  client: Client,
  workspaceId: string,
  specNumber: number,
): Promise<Claim[]> {
  const { data, error } = await client
    .from('latest_claims')
    .select(
      'id, spec_number, criterion_number, name, classname, file, outcome, message, repository, suite, sha, run_id, workflow, received_at',
    )
    .eq('workspace_id', workspaceId)
    .eq('spec_number', specNumber)
    .order('criterion_number')
    .order('name');
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    specNumber: row.spec_number,
    criterionNumber: row.criterion_number,
    name: row.name,
    classname: row.classname,
    file: row.file,
    outcome: row.outcome,
    message: row.message,
    repository: row.repository,
    suite: row.suite,
    sha: row.sha,
    runId: row.run_id,
    workflow: row.workflow,
    receivedAt: row.received_at,
  }));
}

/** Confirms that a reworded criterion's tests check its new wording. */
export async function confirmCriterion(client: Client, id: string): Promise<void> {
  const { error } = await client.rpc('confirm_criterion', { criterion: id });
  if (error) throw refusal(error);
}
