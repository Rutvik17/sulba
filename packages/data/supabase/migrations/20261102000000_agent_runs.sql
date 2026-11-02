-- Sulba's own agents (decision records 63 and 64). A member starts one on a request, and each run
-- is a row here: which agent, the budget it was given and what it cost at list price. A workspace
-- has a monthly limit that only Sulba sets, and no run starts once the month's runs have spent or
-- set aside all of it. The Worker starts the run's session on Claude Managed Agents and, when it
-- ends, writes its work through the functions below. They act as the run's person's agent would:
-- the claims Postgres reads name the person and the agent, so every rule for agents holds.

alter table public.workspaces add column agent_limit_cents integer not null default 0
  check (agent_limit_cents between 0 and 1000000);

create type public.agent_role as enum ('intake');
create type public.agent_run_status as enum ('running', 'done', 'failed', 'stopped');

create table public.agent_runs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces (id) on delete cascade,
  request_id uuid not null,
  role public.agent_role not null,
  status public.agent_run_status not null default 'running',
  -- In US cents: the most the run may spend, and what it spent at the model's list price.
  budget_cents integer not null check (budget_cents > 0),
  cost_cents integer not null default 0 check (cost_cents >= 0),
  -- The run's session on Claude Managed Agents, and the version of the agent it ran.
  session_id text unique,
  agent_version integer check (agent_version > 0),
  -- What the run did, or why it ended without doing it.
  note text check (note is null or char_length(note) between 1 and 500),
  started_by uuid references public.people (id) on delete set null,
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  foreign key (workspace_id, request_id) references public.requests (workspace_id, id) on delete cascade
);

create index agent_runs_by_workspace on public.agent_runs (workspace_id, started_at);
create index agent_runs_by_request on public.agent_runs (request_id, started_at);

-- Each of Sulba's agents and its environment on Claude Managed Agents, with a hash of the
-- definition it was made from, so the Worker updates it only when its definition changes.
create table private.managed_agents (
  name text primary key,
  hash text not null,
  remote_id text not null,
  version integer check (version > 0)
);

alter table private.managed_agents enable row level security;

-- An agent is acting when the token was issued to an OAuth client, or when the claims name one of
-- Sulba's own agents. Only the functions in this file set that claim, inside their transaction;
-- tokens from Supabase's Auth server never carry it.
create or replace function private.by_agent()
returns boolean
language sql
stable
set search_path = ''
as $$
  select (select auth.jwt()) ->> 'client_id' is not null
    or (select auth.jwt()) ->> 'sulba_agent' is not null
$$;

-- Sulba's own agents have no session to end: they act only while one of these functions runs.
create or replace function private.connected()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select not private.by_agent()
    or (select auth.jwt()) ->> 'sulba_agent' is not null
    or exists (
      select from auth.sessions
      where id = ((select auth.jwt()) ->> 'session_id')::uuid and user_id = (select auth.uid())
    )
$$;

create or replace function private.agent_name()
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce(
    (
      select left(btrim(client_name), 64) from auth.oauth_clients
      where id::text = (select auth.jwt()) ->> 'client_id'
    ),
    (select auth.jwt()) ->> 'sulba_agent'
  );
$$;

create or replace function private.name_agent()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.actor_client is not null or (select auth.jwt()) ->> 'sulba_agent' is not null then
    new.actor_agent := (select private.agent_name());
  end if;
  return new;
end;
$$;

-- The agent's name as the workspace sees it, such as "Sulba Intake".
create function private.agent_title(role public.agent_role)
returns text
language sql
immutable
set search_path = ''
as $$
  select 'Sulba ' || initcap(role::text)
$$;

-- What a role may spend on one run, in US cents.
create function private.agent_cap(role public.agent_role)
returns integer
language sql
immutable
set search_path = ''
as $$
  select case role when 'intake' then 100 end
$$;

-- What a workspace's runs started this month (UTC) have spent, and what its running runs may
-- still spend, which is set aside until they end.
create function private.agent_spending(workspace uuid, out spent integer, out reserved integer)
language sql
stable
set search_path = ''
as $$
  select
    coalesce(sum(cost_cents) filter (where status <> 'running'), 0)::integer,
    coalesce(sum(budget_cents) filter (where status = 'running'), 0)::integer
  from public.agent_runs
  where workspace_id = workspace
    and started_at >= date_trunc('month', now() at time zone 'utc') at time zone 'utc'
$$;

revoke execute on function private.agent_title(public.agent_role) from public;
revoke execute on function private.agent_cap(public.agent_role) from public;
revoke execute on function private.agent_spending(uuid) from public;

-- A workspace's limit for the month, and what its runs have spent and set aside, for its members.
create function public.agent_spending(workspace uuid)
returns table (limit_cents integer, spent_cents integer, reserved_cents integer)
language sql
stable
security definer
set search_path = ''
as $$
  select w.agent_limit_cents, s.spent, s.reserved
  from public.workspaces w, private.agent_spending(w.id) s
  where w.id = workspace and access.holds(workspace, 'viewer')
$$;

-- Starts a run of one of Sulba's agents on a request, as a member, and gives its ID. Its budget is
-- the role's cap, or what is left of the workspace's limit this month if that is less. Only people
-- start runs, as only they spend the workspace's money.
create function public.begin_agent_run(request uuid, role public.agent_role)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  asked public.requests;
  allowed integer;
  spending record;
  made uuid;
begin
  select * into asked from public.requests where id = request;
  if not found or not access.holds(asked.workspace_id, 'member') then
    raise exception 'Only members can start Sulba''s agents' using errcode = '42501';
  end if;
  if private.by_agent() then
    raise exception 'An agent can''t start Sulba''s agents. A person does that in Sulba'
      using errcode = '42501';
  end if;
  if asked.status <> 'open' then
    raise exception 'This request is %. Sulba''s agents work on open requests', asked.status
      using errcode = '23514';
  end if;
  -- Runs are counted with the workspace locked, so two started at once can't both spend the
  -- same part of its limit.
  select agent_limit_cents into allowed from public.workspaces where id = asked.workspace_id
  for update;
  if exists (
    select from public.agent_runs r
    where r.request_id = request and r.role = begin_agent_run.role and r.status = 'running'
  ) then
    raise exception '% is already working on this request', private.agent_title(role)
      using errcode = '23505';
  end if;
  select * into spending from private.agent_spending(asked.workspace_id);
  allowed := least(private.agent_cap(role), allowed - spending.spent - spending.reserved);
  if allowed < 10 then
    raise exception 'This workspace has used its agent allowance for this month'
      using errcode = '54000';
  end if;
  insert into public.agent_runs (workspace_id, request_id, role, budget_cents, started_by)
  values (asked.workspace_id, request, role, allowed, (select auth.uid()))
  returning id into made;
  return made;
end;
$$;

-- What the Worker needs to start a run's session: its request, with the questions already asked
-- and answered, and its budget. Only the Worker calls it.
create function public.agent_run_brief(run uuid)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select jsonb_build_object(
    'id', r.id,
    'role', r.role,
    'status', r.status,
    'budget_cents', r.budget_cents,
    'workspace', w.slug,
    'request', jsonb_build_object(
      'number', q.number,
      'title', q.title,
      'body', q.body,
      'questions', coalesce((
        select jsonb_agg(jsonb_build_object('text', a.text, 'answer', a.answer) order by a.asked_at)
        from public.questions a where a.request_id = q.id
      ), '[]')
    )
  )
  from public.agent_runs r
  join public.requests q on q.id = r.request_id
  join public.workspaces w on w.id = r.workspace_id
  where r.id = run
$$;

-- Notes the session the Worker started for a running run. Only the Worker calls it.
create function public.agent_run_started(run uuid, session text, version integer)
returns void
language sql
security definer
set search_path = ''
as $$
  update public.agent_runs set session_id = session, agent_version = version
  where id = run and status = 'running' and session_id is null
$$;

-- Ends a running run with what it cost, and gives whether it was running. Ending twice changes
-- nothing, so the Worker can end a run from each notice of its session. Only the Worker calls it.
create function public.end_agent_run(
  run uuid,
  status public.agent_run_status,
  cost_cents integer,
  note text default null
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
begin
  if status = 'running' then
    raise exception 'A run ends as done, failed or stopped' using errcode = '22023';
  end if;
  update public.agent_runs r
  set status = end_agent_run.status, cost_cents = greatest(end_agent_run.cost_cents, 0),
    note = nullif(left(btrim(end_agent_run.note), 500), ''), ended_at = now()
  where r.id = run and r.status = 'running';
  return found;
end;
$$;

-- Ends an Intake run with the questions it asks the request's writer, asked as the run's person's
-- agent, so the request's rules for agents hold. Gives whether it was running. Only the Worker
-- calls it.
create function public.end_intake_run(run uuid, questions text[], cost_cents integer)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  ran public.agent_runs;
  question text;
  claims text := current_setting('request.jwt.claims', true);
  kind text := current_setting('sulba.actor_kind', true);
begin
  select * into ran from public.agent_runs where id = run and role = 'intake' for update;
  if not found or ran.status <> 'running' then
    return false;
  end if;
  perform set_config(
    'request.jwt.claims',
    jsonb_build_object(
      'sub', ran.started_by, 'role', 'authenticated', 'sulba_agent', private.agent_title(ran.role)
    )::text,
    true
  );
  perform set_config('sulba.actor_kind', 'agent', true);
  foreach question in array coalesce(questions, '{}') loop
    perform public.ask_question(ran.request_id, question);
  end loop;
  perform set_config('request.jwt.claims', coalesce(claims, ''), true);
  perform set_config('sulba.actor_kind', coalesce(kind, ''), true);
  return public.end_agent_run(
    run,
    'done',
    cost_cents,
    case coalesce(cardinality(questions), 0)
      when 0 then 'No questions. The request says what it needs.'
      when 1 then 'Asked 1 question.'
      else format('Asked %s questions.', cardinality(questions))
    end
  );
end;
$$;

-- The agent and environment the Worker made for a definition, and saving them.
create function public.managed_agent(name text)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select jsonb_build_object('hash', hash, 'remote_id', remote_id, 'version', version)
  from private.managed_agents m where m.name = managed_agent.name
$$;

create function public.save_managed_agent(name text, hash text, remote_id text, version integer)
returns void
language sql
security definer
set search_path = ''
as $$
  insert into private.managed_agents (name, hash, remote_id, version)
  values (name, hash, remote_id, version)
  on conflict (name) do update
  set hash = excluded.hash, remote_id = excluded.remote_id, version = excluded.version
$$;

revoke execute on function public.agent_spending(uuid) from public, anon;
revoke execute on function public.begin_agent_run(uuid, public.agent_role) from public, anon;
revoke execute on function public.agent_run_brief(uuid) from public, anon, authenticated;
revoke execute on function public.agent_run_started(uuid, text, integer) from public, anon, authenticated;
revoke execute on function public.end_agent_run(uuid, public.agent_run_status, integer, text)
  from public, anon, authenticated;
revoke execute on function public.end_intake_run(uuid, text[], integer) from public, anon, authenticated;
revoke execute on function public.managed_agent(text) from public, anon, authenticated;
revoke execute on function public.save_managed_agent(text, text, text, integer)
  from public, anon, authenticated;
grant execute on function public.agent_spending(uuid) to authenticated;
grant execute on function public.begin_agent_run(uuid, public.agent_role) to authenticated;
grant execute on function public.agent_run_brief(uuid) to service_role;
grant execute on function public.agent_run_started(uuid, text, integer) to service_role;
grant execute on function public.end_agent_run(uuid, public.agent_run_status, integer, text)
  to service_role;
grant execute on function public.end_intake_run(uuid, text[], integer) to service_role;
grant execute on function public.managed_agent(text) to service_role;
grant execute on function public.save_managed_agent(text, text, text, integer) to service_role;

-- Members read their workspaces' runs. Only begin_agent_run and the Worker's functions write them.
alter table public.agent_runs enable row level security;

revoke all on public.agent_runs from anon, authenticated;
grant select on public.agent_runs to authenticated;

create policy "Members see their workspaces' agent runs" on public.agent_runs
for select to authenticated using (workspace_id in (select access.workspace_ids()));
