/*
  Runs of Sulba's own agents (decision records 63 and 64). A member starts one from the app: the
  Worker asks Postgres for a run as that person, which checks their role and the workspace's
  monthly limit, then starts its session on Claude Managed Agents with the run's budget. Anthropic
  tells the Worker when a session goes idle or ends, and the app asks the Worker to check a run
  while it shows one, so a missed notice changes nothing. Either way the Worker reads the session,
  writes the agent's work through Postgres and records what the run cost. The settings and fetch
  are passed in, so every step can be tested without the network.
*/
import Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';
import * as intake from './intake';

export interface Settings {
  readonly supabaseUrl: string;
  readonly publishableKey: string;
  /** Supabase's secret key, a Worker secret. */
  readonly secretKey: string | undefined;
  /** Anthropic's API key, a Worker secret. */
  readonly anthropicKey: string | undefined;
  /** The secret Anthropic signs its notices to the Worker with, a Worker secret. */
  readonly webhookKey?: string | undefined;
  /** How the Worker reaches Supabase and Anthropic; by default its fetch. */
  readonly fetch?: typeof fetch;
}

/** The sandbox each run's session works in: no network, as Intake only reads and writes files. */
const environment = {
  name: 'Sulba',
  config: { type: 'cloud', networking: { type: 'limited' } },
} as const;

/** What the Worker learns of a run from agent_run_brief. */
interface RunBrief {
  readonly id: string;
  readonly role: 'intake';
  readonly status: string;
  readonly budget_cents: number;
  readonly workspace: string;
  readonly request: intake.Brief;
}

/** A refusal from Postgres, or Supabase out of reach, in words a person can read. */
class Refused extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

const say = (status: number, message: string) => Response.json({ message }, { status });

const started = z.object({ request: z.uuid(), role: z.literal('intake') });
const checked = z.object({ run: z.uuid() });

function anthropic(settings: Settings): Anthropic {
  return new Anthropic({
    apiKey: settings.anthropicKey ?? null,
    webhookKey: settings.webhookKey ?? null,
    ...(settings.fetch ? { fetch: settings.fetch } : {}),
  });
}

/**
 * Calls a Postgres function through the Data API: as a person, with their token, or as the Worker,
 * with Supabase's secret key.
 */
async function rpc<T>(
  settings: Settings,
  name: string,
  args: Record<string, unknown>,
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = token
    ? { apikey: settings.publishableKey, Authorization: `Bearer ${token}` }
    : { apikey: settings.secretKey ?? '' };
  const response = await (settings.fetch ?? fetch)(`${settings.supabaseUrl}/rest/v1/rpc/${name}`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify(args),
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      typeof body === 'object' &&
      body !== null &&
      'message' in body &&
      typeof body.message === 'string'
        ? body.message
        : 'Sulba couldn’t reach its database';
    // Postgres reports a spent allowance as a limit it ran into, which isn't the server's fault.
    throw new Refused(response.status >= 500 && body !== null ? 409 : response.status, message);
  }
  return body as T;
}

async function hashOf(value: unknown): Promise<string> {
  const digest = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(JSON.stringify(value)),
  );
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

interface Made {
  readonly hash: string;
  readonly remote_id: string;
  readonly version: number | null;
}

/**
 * The agent or environment made from a definition: the one made before if the definition hasn't
 * changed, otherwise a new version of it, or the first.
 */
async function ensure(
  settings: Settings,
  name: string,
  definition: unknown,
  make: () => Promise<{ id: string; version?: number }>,
  change: (id: string) => Promise<{ id: string; version?: number }>,
): Promise<{ id: string; version: number | null }> {
  const hash = await hashOf(definition);
  const made = await rpc<Made | null>(settings, 'managed_agent', { name });
  if (made?.hash === hash) return { id: made.remote_id, version: made.version };
  const current = made ? await change(made.remote_id) : await make();
  const version = current.version ?? null;
  await rpc(settings, 'save_managed_agent', { name, hash, remote_id: current.id, version });
  return { id: current.id, version };
}

const ensureEnvironment = (client: Anthropic, settings: Settings) =>
  ensure(
    settings,
    'environment:Sulba',
    environment,
    () => client.beta.environments.create(environment),
    (id) => client.beta.environments.update(id, environment),
  );

const ensureIntake = (client: Anthropic, settings: Settings) =>
  ensure(
    settings,
    intake.definition.name,
    intake.definition,
    () => client.beta.agents.create(intake.definition),
    (id) => client.beta.agents.update(id, intake.definition),
  );

/** The person's access token, from a request the app sent. */
function tokenOf(request: Request): string | undefined {
  return /^Bearer (\S+)$/.exec(request.headers.get('Authorization') ?? '')?.[1];
}

/** Why a request from the app can't be taken, or undefined when it can. */
function refusalOf(request: Request, settings: Settings): Response | undefined {
  // Only Sulba's own pages call these routes, so another site can't spend a workspace's allowance
  // through a person's browser.
  if (request.headers.get('Origin') !== new URL(request.url).origin) {
    return say(403, 'Requests from other sites aren’t taken');
  }
  if (!tokenOf(request)) return say(401, 'Sign in to Sulba to use its agents');
  if (!settings.secretKey || !settings.anthropicKey) {
    return say(503, 'Sulba’s agents aren’t available yet');
  }
  return undefined;
}

/** Starts a run of Intake on a request, for the member who sent it. */
export async function start(request: Request, settings: Settings): Promise<Response> {
  const refusal = refusalOf(request, settings);
  if (refusal) return refusal;
  const asked = started.safeParse(await request.json().catch(() => null));
  if (!asked.success) return say(400, 'Send the request’s ID and the agent to start');

  let run: string;
  try {
    run = await rpc<string>(settings, 'begin_agent_run', asked.data, tokenOf(request));
  } catch (error) {
    if (error instanceof Refused) return say(error.status, error.message);
    throw error;
  }

  try {
    const brief = await rpc<RunBrief>(settings, 'agent_run_brief', { run });
    const client = anthropic(settings);
    const [place, agent] = await Promise.all([
      ensureEnvironment(client, settings),
      ensureIntake(client, settings),
    ]);
    const session = await client.beta.sessions.create({
      agent:
        agent.version === null ? agent.id : { type: 'agent', id: agent.id, version: agent.version },
      environment_id: place.id,
      title: `${brief.workspace} REQ-${brief.request.number}: ${intake.definition.name}`,
      budget: {
        type: 'limit',
        max_list_cost: { amount: String(brief.budget_cents), currency: 'USD' },
      },
      metadata: { sulba_run: run },
      initial_events: [
        {
          type: 'user.define_outcome',
          description: intake.task(brief.request),
          rubric: { type: 'text', content: intake.rubric },
          max_iterations: 2,
        },
      ],
    });
    await rpc(settings, 'agent_run_started', { run, session: session.id, version: agent.version });
  } catch (error) {
    console.error('An agent run didn’t start', error);
    await rpc(settings, 'end_agent_run', {
      run,
      status: 'failed',
      cost_cents: 0,
      note: 'Sulba couldn’t start the agent.',
    }).catch(() => undefined);
    return say(502, 'Sulba couldn’t start the agent. Try again in a minute');
  }
  return Response.json({ run }, { status: 201 });
}

/** A session's list cost, in whole US cents. */
function centsOf(cost: { amount: string; currency: string } | null | undefined): number {
  return cost?.currency === 'USD' ? Number.parseInt(cost.amount, 10) || 0 : 0;
}

type Ending =
  | { readonly status: 'done' }
  | { readonly status: 'failed' | 'stopped'; readonly note: string };

/** How a session that isn't running ended, from its latest idle event and its outcome. */
async function endingOf(
  client: Anthropic,
  session: Anthropic.Beta.Sessions.BetaManagedAgentsSession,
): Promise<Ending> {
  if (session.status === 'terminated') {
    return { status: 'failed', note: 'The agent’s session ended before it finished.' };
  }
  const events = await client.beta.sessions.events.list(session.id, { order: 'desc', limit: 50 });
  const idle = events.data.find((event) => event.type === 'session.status_idle');
  const reason = idle && 'stop_reason' in idle ? idle.stop_reason.type : undefined;
  if (reason === 'budget_reached') return { status: 'stopped', note: 'Reached its budget.' };
  if (reason !== 'end_turn') {
    return { status: 'failed', note: 'The agent stopped before it finished.' };
  }
  const last = session.outcome_evaluations.at(-1);
  if (last?.result === 'failed') {
    return { status: 'failed', note: 'The agent couldn’t do what was asked.' };
  }
  return { status: 'done' };
}

/** The questions Intake wrote to its session's outputs, checked, or undefined if there are none. */
async function questionsOf(client: Anthropic, sessionId: string): Promise<string[] | undefined> {
  const files = await client.beta.files.list({
    scope_id: sessionId,
    betas: ['managed-agents-2026-04-01'],
  });
  const file = files.data.find((each) => each.filename.split('/').at(-1) === intake.outputFile);
  if (!file) return undefined;
  const content = await client.beta.files.download(file.id);
  const parsed = intake.handedIn.safeParse(await content.json().catch(() => null));
  if (!parsed.success) return undefined;
  const seen = new Set<string>();
  return parsed.data.questions.filter((question) => {
    const key = question.toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/**
 * Settles a session that went idle or ended: writes its run's work and what it cost, once. A
 * session still running, or not one of Sulba's runs, is left alone.
 */
export async function settle(sessionId: string, settings: Settings): Promise<void> {
  const client = anthropic(settings);
  const session = await client.beta.sessions.retrieve(sessionId);
  const run = session.metadata.sulba_run;
  if (!run || session.status === 'running' || session.status === 'rescheduling') return;
  const cost = centsOf(session.usage.list_cost);
  const ending = await endingOf(client, session);
  const end = (status: 'failed' | 'stopped', note: string) =>
    rpc(settings, 'end_agent_run', { run, status, cost_cents: cost, note });
  if (ending.status !== 'done') {
    await end(ending.status, ending.note);
    return;
  }
  const questions = await questionsOf(client, sessionId);
  if (!questions) {
    await end('failed', 'The agent didn’t hand in its questions.');
    return;
  }
  try {
    await rpc(settings, 'end_intake_run', { run, questions, cost_cents: cost });
  } catch (error) {
    if (!(error instanceof Refused)) throw error;
    await end('failed', error.message);
  }
}

/**
 * Checks a run for a member who can see it, as the app does while it shows a running one, so the
 * run settles even when a notice from Anthropic is lost.
 */
export async function check(request: Request, settings: Settings): Promise<Response> {
  const refusal = refusalOf(request, settings);
  if (refusal) return refusal;
  const asked = checked.safeParse(await request.json().catch(() => null));
  if (!asked.success) return say(400, 'Send the run’s ID');
  const response = await (settings.fetch ?? fetch)(
    `${settings.supabaseUrl}/rest/v1/agent_runs?select=status,session_id&id=eq.${asked.data.run}`,
    { headers: { apikey: settings.publishableKey, Authorization: `Bearer ${tokenOf(request)}` } },
  );
  const rows = response.ok
    ? ((await response.json()) as { status: string; session_id: string | null }[])
    : [];
  const [seen] = rows;
  if (!seen) return say(404, 'There is no such run in your workspaces');
  if (seen.status === 'running' && seen.session_id) await settle(seen.session_id, settings);
  return new Response(null, { status: 204 });
}

/** Takes Anthropic's notice that a session changed, and settles the session if it stopped. */
export async function receive(request: Request, settings: Settings): Promise<Response> {
  if (!settings.secretKey || !settings.anthropicKey || !settings.webhookKey) {
    return say(503, 'Sulba’s agents aren’t available yet');
  }
  const body = await request.text();
  let event: Anthropic.Beta.Webhooks.BetaWebhookEvent;
  try {
    event = anthropic(settings).beta.webhooks.unwrap(body, {
      headers: Object.fromEntries(request.headers),
    });
  } catch {
    return say(400, 'The notice isn’t signed by Anthropic');
  }
  if (
    event.data.type === 'session.status_idled' ||
    event.data.type === 'session.status_terminated'
  ) {
    await settle(event.data.id, settings);
  }
  return new Response(null, { status: 204 });
}
