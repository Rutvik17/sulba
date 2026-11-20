// Runs of Sulba's own agents on a request, and what a workspace's runs have spent this month
// (decision records 63 and 64). A member starts a run through the site's Worker, which holds the
// keys; Postgres keeps each run with its budget and cost, and members read them here.
import type { Client } from './client.ts';
import type { Database } from './database.ts';
import { Refusal, refusal } from './refusal.ts';

export type AgentRole = Database['public']['Enums']['agent_role'];
export type AgentRunStatus = Database['public']['Enums']['agent_run_status'];

export interface AgentRun {
  readonly id: string;
  readonly role: AgentRole;
  readonly status: AgentRunStatus;
  /** In US cents: the most the run may spend, and what it spent. */
  readonly budgetCents: number;
  readonly costCents: number;
  readonly note: string | null;
  readonly startedBy: string | null;
  readonly startedAt: string;
  readonly endedAt: string | null;
}

/** A workspace's limit for the month, in US cents, and what its runs spent and set aside. */
export interface Spending {
  readonly limitCents: number;
  readonly spentCents: number;
  readonly reservedCents: number;
}

export const agentNames: Record<AgentRole, string> = { intake: 'Sulba Intake' };

/** What each agent does, as the request's page says it. */
export const agentJobs: Record<AgentRole, string> = {
  intake: 'Reads the request and asks its writer what it needs to know before specs are drafted.',
};

/** A request's runs, the newest first. */
export async function runsOf(client: Client, requestId: string): Promise<AgentRun[]> {
  const { data, error } = await client
    .from('agent_runs')
    .select('id, role, status, budget_cents, cost_cents, note, started_by, started_at, ended_at')
    .eq('request_id', requestId)
    .order('started_at', { ascending: false });
  if (error) throw refusal(error);
  return data.map((row) => ({
    id: row.id,
    role: row.role,
    status: row.status,
    budgetCents: row.budget_cents,
    costCents: row.cost_cents,
    note: row.note,
    startedBy: row.started_by,
    startedAt: row.started_at,
    endedAt: row.ended_at,
  }));
}

/** What a workspace's runs have spent this month, against its limit. */
export async function spendingOf(client: Client, workspaceId: string): Promise<Spending> {
  const { data, error } = await client.rpc('agent_spending', { workspace: workspaceId });
  if (error) throw refusal(error);
  const [row] = data;
  return {
    limitCents: row?.limit_cents ?? 0,
    spentCents: row?.spent_cents ?? 0,
    reservedCents: row?.reserved_cents ?? 0,
  };
}

/** US cents as dollars: $0.37, $25.00. */
export function dollars(cents: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(cents / 100);
}

/** Calls one of the Worker's agent routes as the signed-in person. */
async function callWorker(client: Client, path: string, body: unknown): Promise<Response> {
  const { data } = await client.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Refusal('Sign in again to use Sulba’s agents.');
  let response: Response;
  try {
    response = await fetch(path, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Refusal('Sulba couldn’t reach its agents just now. Try again.');
  }
  if (!response.ok) {
    const said = (await response.json().catch(() => null)) as { message?: unknown } | null;
    const message =
      typeof said?.message === 'string' ? said.message : 'Sulba couldn’t do that just now';
    throw new Refusal(/[.!?]$/.test(message) ? message : `${message}.`);
  }
  return response;
}

/** Starts one of Sulba's agents on a request, and gives the run's ID. */
export async function startRun(
  client: Client,
  requestId: string,
  role: AgentRole,
): Promise<string> {
  const response = await callWorker(client, '/api/agents/runs', { request: requestId, role });
  const { run } = (await response.json()) as { run: string };
  return run;
}

/** Asks the Worker to check a running run, which settles it if its agent has finished. */
export async function checkRun(client: Client, runId: string): Promise<void> {
  await callWorker(client, '/api/agents/check', { run: runId });
}
