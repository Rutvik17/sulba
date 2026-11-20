import { createHmac } from 'node:crypto';
import { describe, expect, it } from 'vitest';
import { check, receive, type Settings, settle, start } from './runs';

// Stand-ins for Supabase's Data API and Claude Managed Agents, so a run starts, settles and costs
// nothing.

const run = 'a1000000-0000-4000-8000-000000000001';
const requestId = 'b2000000-0000-4000-8000-000000000002';
const origin = 'https://sulba.test';
const webhookKey = `whsec_${Buffer.from('a'.repeat(32)).toString('base64')}`;

interface Call {
  readonly method: string;
  readonly url: URL;
  readonly body: unknown;
}

interface Session {
  id: string;
  status: string;
  metadata: Record<string, string>;
  usage: { list_cost: { amount: string; currency: string } | null };
  outcome_evaluations: { result: string }[];
}

interface Options {
  /** What begin_agent_run answers: a run, or a refusal. */
  begin?: { status: number; body: unknown };
  /** The session settle reads. */
  session?: Partial<Session>;
  /** The latest idle event's stop reason. */
  stopReason?: string;
  /** The files the session handed in, by name. */
  files?: Record<string, string>;
  /** What creating a session answers, when it fails. */
  sessionFails?: boolean;
  /** The runs the person can see. */
  visible?: { status: string; session_id: string | null }[];
}

function standIn(options: Options = {}) {
  const calls: Call[] = [];
  const kept = new Map<string, { hash: string; remote_id: string; version: number | null }>();
  const session: Session = {
    id: 'sesn_1',
    status: 'idle',
    metadata: { sulba_run: run },
    usage: { list_cost: { amount: '37', currency: 'USD' } },
    outcome_evaluations: [{ result: 'satisfied' }],
    ...options.session,
  };
  const files = options.files ?? {
    'questions.json': JSON.stringify({
      questions: [
        'Do members pay when they book?',
        'do members pay when they book?',
        'Which classes are bookable?',
      ],
    }),
  };
  const json = (body: unknown, status = 200) => Response.json(body, { status });

  const fetch = async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
    const request = new Request(input, init);
    const url = new URL(request.url);
    const text = request.method === 'GET' ? '' : await request.text();
    const body = text ? JSON.parse(text) : undefined;
    calls.push({ method: request.method, url, body });

    if (url.origin === 'https://db.test') {
      const name = url.pathname.replace('/rest/v1/rpc/', '');
      switch (name) {
        case 'begin_agent_run':
          return options.begin ? json(options.begin.body, options.begin.status) : json(run);
        case 'agent_run_brief':
          return json({
            id: run,
            role: 'intake',
            status: 'running',
            budget_cents: 100,
            workspace: 'acme',
            request: {
              number: 2,
              title: 'A booking app',
              body: 'Members book classes from their phones.',
              questions: [{ text: 'Is it for one gym?', answer: 'Yes, one.' }],
            },
          });
        case 'managed_agent':
          return json(kept.get(body.name) ?? null);
        case 'save_managed_agent':
          kept.set(body.name, {
            hash: body.hash,
            remote_id: body.remote_id,
            version: body.version,
          });
          return new Response(null, { status: 204 });
        case 'agent_run_started':
        case 'end_agent_run':
        case 'end_intake_run':
          return json(true);
        case '/rest/v1/agent_runs':
          return json(options.visible ?? []);
      }
    }
    if (url.origin === 'https://api.anthropic.com') {
      const path = url.pathname;
      if (request.method === 'POST' && path === '/v1/environments') {
        return json({ id: 'env_1', type: 'environment' });
      }
      if (request.method === 'POST' && path === '/v1/agents') {
        return json({ id: 'agent_1', version: 1, type: 'agent' });
      }
      if (request.method === 'POST' && path === '/v1/sessions') {
        return options.sessionFails
          ? json({ type: 'error', error: { type: 'invalid_request_error', message: 'No' } }, 400)
          : json({ ...session, status: 'running' });
      }
      if (path === `/v1/sessions/${session.id}`) return json(session);
      if (path === `/v1/sessions/${session.id}/events`) {
        return json({
          data: [
            { type: 'span.model_request_end', id: 'sevt_2' },
            {
              type: 'session.status_idle',
              id: 'sevt_1',
              stop_reason: { type: options.stopReason ?? 'end_turn' },
            },
          ],
          next_page: null,
        });
      }
      if (path === '/v1/files') {
        return json({
          data: Object.keys(files).map((name, index) => ({ id: `file_${index}`, filename: name })),
          next_page: null,
        });
      }
      const download = /^\/v1\/files\/file_(\d+)\/content$/.exec(path);
      if (download) return new Response(Object.values(files)[Number(download[1])]);
    }
    return json({ message: `No stand-in for ${request.method} ${url}` }, 404);
  };

  const settings: Settings = {
    supabaseUrl: 'https://db.test',
    publishableKey: 'sb_publishable_test',
    secretKey: 'sb_secret_test',
    anthropicKey: 'sk-ant-test',
    webhookKey,
    fetch,
  };
  const rpcs = () =>
    calls
      .filter((call) => call.url.pathname.startsWith('/rest/v1/rpc/'))
      .map((call) => ({ name: call.url.pathname.replace('/rest/v1/rpc/', ''), args: call.body }));
  const anthropic = () =>
    calls
      .filter((call) => call.url.origin === 'https://api.anthropic.com')
      .map((call) => `${call.method} ${call.url.pathname}`);
  return { settings, calls, rpcs, anthropic, session };
}

/** What a session is created with, as the stand-in reads it. */
interface Created {
  readonly agent: unknown;
  readonly environment_id: string;
  readonly budget: unknown;
  readonly metadata: unknown;
  readonly initial_events: readonly {
    type: string;
    description: string;
    rubric: { type: string };
  }[];
}

const fromApp = (path: string, body: unknown, headers: Record<string, string> = {}) =>
  new Request(`${origin}${path}`, {
    method: 'POST',
    headers: { Origin: origin, Authorization: 'Bearer person-token', ...headers },
    body: JSON.stringify(body),
  });

describe('start', () => {
  it('takes requests only from Sulba’s own pages, from a person signed in, once its keys are set', async () => {
    const { settings } = standIn();
    const asked = { request: requestId, role: 'intake' };
    expect(
      (await start(fromApp('/api/agents/runs', asked, { Origin: 'https://evil.test' }), settings))
        .status,
    ).toBe(403);
    expect(
      (await start(fromApp('/api/agents/runs', asked, { Authorization: '' }), settings)).status,
    ).toBe(401);
    expect(
      (await start(fromApp('/api/agents/runs', asked), { ...settings, anthropicKey: undefined }))
        .status,
    ).toBe(503);
    expect((await start(fromApp('/api/agents/runs', { request: 'REQ-2' }), settings)).status).toBe(
      400,
    );
  });

  it('passes on what Postgres says when it refuses the run', async () => {
    const { settings, anthropic } = standIn({
      begin: {
        status: 500,
        body: {
          code: '54000',
          message: 'This workspace has used its agent allowance for this month',
        },
      },
    });
    const response = await start(
      fromApp('/api/agents/runs', { request: requestId, role: 'intake' }),
      settings,
    );
    expect(response.status).toBe(409);
    expect(await response.json()).toEqual({
      message: 'This workspace has used its agent allowance for this month',
    });
    expect(anthropic()).toEqual([]);
  });

  it('asks for the run as the person, then starts its session with the run’s budget', async () => {
    const { settings, calls, rpcs, anthropic } = standIn();
    const response = await start(
      fromApp('/api/agents/runs', { request: requestId, role: 'intake' }),
      settings,
    );
    expect(response.status).toBe(201);
    expect(await response.json()).toEqual({ run });

    const begun = calls.find((call) => call.url.pathname.endsWith('/begin_agent_run'));
    expect(begun?.body).toEqual({ request: requestId, role: 'intake' });
    // The agent and its environment are made at once, in either order.
    expect(anthropic().sort()).toEqual([
      'POST /v1/agents',
      'POST /v1/environments',
      'POST /v1/sessions',
    ]);

    const created = calls.find((call) => call.url.pathname === '/v1/sessions')?.body as Created;
    expect(created.agent).toEqual({ type: 'agent', id: 'agent_1', version: 1 });
    expect(created.environment_id).toBe('env_1');
    expect(created.budget).toEqual({
      type: 'limit',
      max_list_cost: { amount: '100', currency: 'USD' },
    });
    expect(created.metadata).toEqual({ sulba_run: run });
    expect(created.initial_events).toHaveLength(1);
    const [kickoff] = created.initial_events;
    if (!kickoff) throw new Error('The session starts with its task');
    expect(kickoff.type).toBe('user.define_outcome');
    expect(kickoff.description).toContain('REQ-2: A booking app');
    expect(kickoff.description).toContain('- Is it for one gym?\n  Yes, one.');
    expect(kickoff.rubric.type).toBe('text');
    expect(rpcs().at(-1)).toEqual({
      name: 'agent_run_started',
      args: { run, session: 'sesn_1', version: 1 },
    });
  });

  it('makes the agent and its environment once, while their definitions stay the same', async () => {
    const { settings, anthropic } = standIn();
    await start(fromApp('/api/agents/runs', { request: requestId, role: 'intake' }), settings);
    await start(fromApp('/api/agents/runs', { request: requestId, role: 'intake' }), settings);
    expect(anthropic().sort()).toEqual([
      'POST /v1/agents',
      'POST /v1/environments',
      'POST /v1/sessions',
      'POST /v1/sessions',
    ]);
  });

  it('ends the run as failed when its session can’t start', async () => {
    const { settings, rpcs } = standIn({ sessionFails: true });
    const response = await start(
      fromApp('/api/agents/runs', { request: requestId, role: 'intake' }),
      settings,
    );
    expect(response.status).toBe(502);
    expect(rpcs().at(-1)).toEqual({
      name: 'end_agent_run',
      args: { run, status: 'failed', cost_cents: 0, note: 'Sulba couldn’t start the agent.' },
    });
  });
});

describe('settle', () => {
  it('asks the questions Intake handed in, once each, with what the run cost', async () => {
    const { settings, rpcs } = standIn();
    await settle('sesn_1', settings);
    expect(rpcs()).toEqual([
      {
        name: 'end_intake_run',
        args: {
          run,
          questions: ['Do members pay when they book?', 'Which classes are bookable?'],
          cost_cents: 37,
        },
      },
    ]);
  });

  it('stops a run that reached its budget', async () => {
    const { settings, rpcs } = standIn({
      stopReason: 'budget_reached',
      session: { usage: { list_cost: { amount: '101', currency: 'USD' } } },
    });
    await settle('sesn_1', settings);
    expect(rpcs()).toEqual([
      {
        name: 'end_agent_run',
        args: { run, status: 'stopped', cost_cents: 101, note: 'Reached its budget.' },
      },
    ]);
  });

  it('fails a run that handed in nothing it can read', async () => {
    for (const files of [{}, { 'questions.json': '{"questions": "Do members pay?"}' }]) {
      const { settings, rpcs } = standIn({ files });
      await settle('sesn_1', settings);
      expect(rpcs()).toEqual([
        {
          name: 'end_agent_run',
          args: {
            run,
            status: 'failed',
            cost_cents: 37,
            note: 'The agent didn’t hand in its questions.',
          },
        },
      ]);
    }
  });

  it('fails a run whose grader found the work couldn’t meet its rubric', async () => {
    const { settings, rpcs } = standIn({
      session: { outcome_evaluations: [{ result: 'failed' }] },
    });
    await settle('sesn_1', settings);
    expect(rpcs()[0]?.args).toMatchObject({
      status: 'failed',
      note: 'The agent couldn’t do what was asked.',
    });
  });

  it('leaves a running session, and one that isn’t a run of Sulba’s, alone', async () => {
    for (const session of [{ status: 'running' }, { metadata: {} }]) {
      const { settings, rpcs } = standIn({ session });
      await settle('sesn_1', settings);
      expect(rpcs()).toEqual([]);
    }
  });
});

describe('check', () => {
  it('settles a running run the person can see', async () => {
    const { settings, rpcs, calls } = standIn({
      visible: [{ status: 'running', session_id: 'sesn_1' }],
    });
    const response = await check(fromApp('/api/agents/check', { run }), settings);
    expect(response.status).toBe(204);
    const read = calls.find((call) => call.url.pathname === '/rest/v1/agent_runs');
    expect(read?.url.searchParams.get('id')).toBe(`eq.${run}`);
    expect(rpcs().map((call) => call.name)).toEqual(['end_intake_run']);
  });

  it('says there’s no such run when the person can’t see it', async () => {
    const { settings } = standIn({ visible: [] });
    expect((await check(fromApp('/api/agents/check', { run }), settings)).status).toBe(404);
  });
});

describe('receive', () => {
  /** A notice signed as Standard Webhooks signs one. */
  const notice = (event: unknown, key = webhookKey) => {
    const body = JSON.stringify(event);
    const id = 'whe_1';
    const timestamp = String(Math.floor(Date.now() / 1000));
    const secret = Buffer.from(key.replace(/^whsec_/, ''), 'base64');
    const signature = createHmac('sha256', secret)
      .update(`${id}.${timestamp}.${body}`)
      .digest('base64');
    return new Request(`${origin}/api/agents/events`, {
      method: 'POST',
      headers: {
        'webhook-id': id,
        'webhook-timestamp': timestamp,
        'webhook-signature': `v1,${signature}`,
      },
      body,
    });
  };
  const idled = {
    type: 'event',
    id: 'whe_1',
    created_at: new Date().toISOString(),
    data: { type: 'session.status_idled', id: 'sesn_1', organization_id: 'o', workspace_id: 'w' },
  };

  it('settles the session a signed notice names', async () => {
    const { settings, rpcs } = standIn();
    expect((await receive(notice(idled), settings)).status).toBe(204);
    expect(rpcs().map((call) => call.name)).toEqual(['end_intake_run']);
  });

  it('refuses a notice Anthropic didn’t sign, and takes none without its secret', async () => {
    const { settings, rpcs } = standIn();
    const forged = notice(idled, `whsec_${Buffer.from('b'.repeat(32)).toString('base64')}`);
    expect((await receive(forged, settings)).status).toBe(400);
    expect((await receive(notice(idled), { ...settings, webhookKey: undefined })).status).toBe(503);
    expect(rpcs()).toEqual([]);
  });

  it('takes other notices without settling anything', async () => {
    const { settings, anthropic } = standIn();
    const created = { ...idled, data: { ...idled.data, type: 'agent.created' } };
    expect((await receive(notice(created), settings)).status).toBe(204);
    expect(anthropic()).toEqual([]);
  });
});
