-- Tasks: an approved spec split into work that a person, or an agent for its person, takes
-- (decision record 61). Each has a number in its workspace, TASK-7, a role, Markdown instructions
-- and the spec's criteria it covers. One taker at a time, who hands in one pull request in one of
-- the workspace's repositories. Only people mark a task done or cancel it.

create type public.task_role as enum ('build', 'test', 'review', 'document');
create type public.task_status as enum (
  'open', 'in_progress', 'blocked', 'in_review', 'done', 'canceled'
);

create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces (id) on delete cascade,
  number integer not null check (number > 0),
  spec_id uuid not null,
  title text not null check (char_length(title) between 1 and 200 and title = btrim(title)),
  role public.task_role not null default 'build',
  status public.task_status not null default 'open',
  -- Markdown: what to do, where, and what done means.
  body text not null default '' check (char_length(body) <= 50000),
  -- Who has it: a person, and the name the agent registered when an agent took it for them.
  taken_by uuid references public.people (id) on delete set null,
  taken_by_agent text,
  taken_at timestamptz,
  -- Why it's blocked, or what its taker said when they handed it in.
  note text check (note is null or (char_length(note) between 1 and 2000 and note = btrim(note))),
  pull_request text check (
    pull_request ~ '^https://github\.com/[A-Za-z0-9-]{1,100}/[A-Za-z0-9_.-]{1,100}/pull/[1-9][0-9]{0,9}$'
  ),
  created_by uuid references public.people (id) on delete set null,
  created_by_agent text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, number),
  unique (workspace_id, id),
  foreign key (workspace_id, spec_id) references public.specs (workspace_id, id) on delete cascade,
  -- Work under way has a taker; an open task has none.
  check (status in ('done', 'canceled') or (status = 'open') = (taken_at is null))
);

create index tasks_by_spec on public.tasks (spec_id);

-- The spec's criteria a task covers, which its pull request's tests are to prove.
create table public.task_criteria (
  workspace_id uuid not null,
  task_id uuid not null,
  criterion_id uuid not null references public.criteria (id) on delete cascade,
  primary key (task_id, criterion_id),
  foreign key (workspace_id, task_id) references public.tasks (workspace_id, id) on delete cascade
);

create index task_criteria_by_workspace on public.task_criteria (workspace_id);
create index task_criteria_by_criterion on public.task_criteria (criterion_id);

create table private.task_numbers (
  workspace_id uuid primary key references public.workspaces (id) on delete cascade,
  last integer not null
);

alter table private.task_numbers enable row level security;

create trigger record_event after insert or update or delete on public.tasks
for each row execute function private.record_event('task', 'id', 'body');

create trigger touch before update on public.tasks
for each row execute function private.touch();

-- Makes a task from an approved spec and gives its number. Members and their agents write tasks;
-- `criteria` are the numbers of the spec's criteria it covers. A spec holds at most 100 tasks and
-- a workspace 5,000.
create function public.create_task(
  spec uuid,
  title text,
  role public.task_role default 'build',
  body text default '',
  criteria integer[] default '{}'
)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  found_spec public.specs;
  given integer;
  made uuid;
  missing integer;
begin
  select * into found_spec from public.specs where id = spec;
  if not found or not access.holds(found_spec.workspace_id, 'member') then
    raise exception 'Only members can write tasks' using errcode = '42501';
  end if;
  if found_spec.status not in ('approved', 'implemented') then
    raise exception 'This spec is %. Tasks are written once it''s approved',
      replace(found_spec.status::text, '_', ' ') using errcode = '23514';
  end if;
  if (select count(*) from public.tasks where spec_id = spec) >= 100 then
    raise exception 'A spec has at most 100 tasks' using errcode = '54000';
  end if;
  if (select count(*) from public.tasks where workspace_id = found_spec.workspace_id) >= 5000 then
    raise exception 'A workspace can hold at most 5,000 tasks' using errcode = '54000';
  end if;
  select n into missing from unnest(criteria) n
  where not exists (select from public.criteria c where c.spec_id = spec and c.number = n)
  limit 1;
  if missing is not null then
    raise exception 'This spec has no AC-%', missing using errcode = 'P0002';
  end if;
  insert into private.task_numbers (workspace_id, last) values (found_spec.workspace_id, 1)
  on conflict (workspace_id) do update set last = private.task_numbers.last + 1
  returning last into given;
  insert into public.tasks (
    workspace_id, number, spec_id, title, role, body, created_by, created_by_agent
  )
  values (
    found_spec.workspace_id,
    given,
    spec,
    btrim(create_task.title),
    role,
    body,
    (select auth.uid()),
    private.agent_name()
  )
  returning id into made;
  insert into public.task_criteria (workspace_id, task_id, criterion_id)
  select found_spec.workspace_id, made, c.id from public.criteria c
  where c.spec_id = spec and c.number = any (criteria);
  return given;
end;
$$;

-- Moves a task on. Anyone may take an open task, which makes them, or the agent's person, its
-- taker. Its taker blocks it with a note, resumes it, hands it in with its pull request, or
-- releases it to the open list; a member may do any of these for a task someone else holds, but
-- an agent only for its own. Only a person marks it done, cancels it, or opens it again.
create function public.update_task(
  task uuid,
  status public.task_status,
  note text default null,
  pull_request text default null
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  found_task public.tasks;
  agent boolean := private.by_agent();
  said text := nullif(btrim(update_task.note), '');
  link text := nullif(btrim(update_task.pull_request), '');
  repository text;
begin
  select * into found_task from public.tasks where id = task for update;
  if not found or not access.holds(found_task.workspace_id, 'member') then
    raise exception 'Only members can work on tasks' using errcode = '42501';
  end if;
  if status = found_task.status then
    raise exception 'TASK-% is already %', found_task.number, replace(status::text, '_', ' ')
      using errcode = '23514';
  end if;
  if agent and status in ('done', 'canceled') then
    raise exception 'An agent can''t mark a task done or cancel it. A person does that in Sulba'
      using errcode = '42501';
  end if;
  if agent and found_task.status in ('done', 'canceled') then
    raise exception 'An agent can''t open a % task again. A person does that in Sulba',
      found_task.status using errcode = '42501';
  end if;
  if agent and found_task.status <> 'open' and found_task.taken_by is distinct from (select auth.uid()) then
    raise exception 'TASK-% is taken by someone else', found_task.number using errcode = '42501';
  end if;
  if status = 'in_progress' and found_task.status = 'open' then
    update public.tasks
    set status = 'in_progress', taken_by = (select auth.uid()), taken_by_agent = private.agent_name(),
      taken_at = now(), note = null
    where id = task;
    return;
  end if;
  if status = 'open' then
    update public.tasks
    set status = 'open', taken_by = null, taken_by_agent = null, taken_at = null, note = said,
      pull_request = case when found_task.status in ('done', 'canceled') then found_task.pull_request end
    where id = task;
    return;
  end if;
  if found_task.status in ('done', 'canceled') then
    raise exception 'TASK-% is %. Open it again first', found_task.number, found_task.status
      using errcode = '23514';
  end if;
  if found_task.status = 'open' and status not in ('done', 'canceled') then
    raise exception 'TASK-% is open. Take it first', found_task.number using errcode = '23514';
  end if;
  if status = 'blocked' and said is null then
    raise exception 'Say what blocks it' using errcode = '23514';
  end if;
  if status = 'in_review' then
    link := coalesce(link, found_task.pull_request);
    if link is null then
      raise exception 'Name the pull request that holds the work' using errcode = '23514';
    end if;
    if link !~ '^https://github\.com/[A-Za-z0-9-]{1,100}/[A-Za-z0-9_.-]{1,100}/pull/[1-9][0-9]{0,9}$' then
      raise exception 'A pull request''s address looks like https://github.com/owner/repo/pull/12'
        using errcode = '22023';
    end if;
    repository := lower(split_part(link, '/', 4) || '/' || split_part(link, '/', 5));
    if not exists (
      select from public.repositories
      where workspace_id = found_task.workspace_id and lower(name) = repository
    ) then
      raise exception '% isn''t one of this workspace''s repositories', repository
        using errcode = '23514';
    end if;
  end if;
  update public.tasks
  set status = update_task.status,
    note = case
      when update_task.status in ('blocked', 'in_review') then said
      when update_task.status = 'in_progress' then null
      else coalesce(said, found_task.note)
    end,
    pull_request = case when update_task.status = 'in_review' then link else found_task.pull_request end
  where id = task;
end;
$$;

revoke execute on function public.create_task(uuid, text, public.task_role, text, integer[])
  from public, anon;
revoke execute on function public.update_task(uuid, public.task_status, text, text)
  from public, anon;
grant execute on function public.create_task(uuid, text, public.task_role, text, integer[])
  to authenticated;
grant execute on function public.update_task(uuid, public.task_status, text, text)
  to authenticated;

-- Everyone in a workspace reads its tasks; members, and their agents, change a task's title, role
-- and instructions. A task isn't deleted: it's canceled, and keeps its number and history. The
-- rest changes only through the functions above.
alter table public.tasks enable row level security;
alter table public.task_criteria enable row level security;

revoke all on public.tasks, public.task_criteria from anon, authenticated;
grant select on public.tasks, public.task_criteria to authenticated;
grant update (title, role, body) on public.tasks to authenticated;

create policy "Members see their workspaces' tasks" on public.tasks
for select to authenticated using (workspace_id in (select access.workspace_ids()));

create policy "Members change tasks" on public.tasks
for update to authenticated
using (workspace_id in (select access.workspace_ids('member')))
with check (workspace_id in (select access.workspace_ids('member')));

create policy "Members see their workspaces' tasks' criteria" on public.task_criteria
for select to authenticated using (workspace_id in (select access.workspace_ids()));
