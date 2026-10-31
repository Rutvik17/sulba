-- Requests: what someone wants built, in their own words, before it's written as specs (decision
-- record 60). Each has a number in its workspace, REQ-3. An agent reads a request, asks its writer
-- what it needs to know, and drafts specs from it, each naming the request it came from. Only
-- people write and change requests, answer questions, and decide a request is planned or closed.

create type public.request_status as enum ('open', 'planned', 'closed');

create table public.requests (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces (id) on delete cascade,
  number integer not null check (number > 0),
  title text not null check (char_length(title) between 1 and 200 and title = btrim(title)),
  status public.request_status not null default 'open',
  -- Markdown: what the writer wants, for whom, and anything it must work with.
  body text not null default '' check (char_length(body) <= 50000),
  created_by uuid references public.people (id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, number),
  unique (workspace_id, id)
);

create table public.questions (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null,
  request_id uuid not null,
  text text not null check (char_length(text) between 1 and 1000 and text = btrim(text)),
  answer text check (answer is null or (char_length(answer) between 1 and 5000 and answer = btrim(answer))),
  asked_by uuid references public.people (id) on delete set null,
  -- The name the agent that asked registered with, when an agent asked for its person.
  asked_by_agent text,
  answered_by uuid references public.people (id) on delete set null,
  asked_at timestamptz not null default now(),
  answered_at timestamptz,
  updated_at timestamptz not null default now(),
  foreign key (workspace_id, request_id) references public.requests (workspace_id, id) on delete cascade
);

create index questions_by_workspace on public.questions (workspace_id);
create index questions_by_request on public.questions (request_id, asked_at);

-- The request a spec was drafted from, in the same workspace.
alter table public.specs add column request_id uuid;
alter table public.specs add foreign key (workspace_id, request_id)
  references public.requests (workspace_id, id) on delete set null (request_id);
create index specs_by_request on public.specs (request_id) where request_id is not null;

-- The last number given in each workspace, so a number is never given twice.
create table private.request_numbers (
  workspace_id uuid primary key references public.workspaces (id) on delete cascade,
  last integer not null
);

alter table private.request_numbers enable row level security;

create trigger record_event after insert or update or delete on public.requests
for each row execute function private.record_event('request', 'id', 'body');
create trigger record_event after insert or update or delete on public.questions
for each row execute function private.record_event('question', 'id');

create trigger touch before update on public.requests
for each row execute function private.touch();
create trigger touch before update on public.questions
for each row execute function private.touch();

-- A request is its writer's words, and its status a person's decision.
create trigger refuse_agents before insert or update or delete on public.requests
for each row execute function private.refuse_agents(
  'An agent can''t write or change a request. A person does that in Sulba'
);

-- Makes a request and gives its number. Members and above write requests; a workspace holds at
-- most 1,000.
create function public.create_request(workspace uuid, title text, body text default '')
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  given integer;
begin
  if not access.holds(workspace, 'member') then
    raise exception 'Only members can write requests' using errcode = '42501';
  end if;
  if (select count(*) from public.requests where workspace_id = workspace) >= 1000 then
    raise exception 'A workspace can hold at most 1,000 requests' using errcode = '54000';
  end if;
  insert into private.request_numbers (workspace_id, last) values (workspace, 1)
  on conflict (workspace_id) do update set last = private.request_numbers.last + 1
  returning last into given;
  insert into public.requests (workspace_id, number, title, body, created_by)
  values (workspace, given, btrim(create_request.title), create_request.body, (select auth.uid()));
  return given;
end;
$$;

-- The name the calling agent registered with, or null for a person.
create function private.agent_name()
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select left(btrim(client_name), 64) from auth.oauth_clients
  where id::text = (select auth.jwt()) ->> 'client_id';
$$;

revoke execute on function private.agent_name() from public;

-- Asks a request's writer a question, as a member or a member's agent, while the request is open.
-- A request holds at most 100.
create function public.ask_question(request uuid, text text)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  asked public.requests;
  made uuid;
begin
  select * into asked from public.requests where id = request;
  if not found or not access.holds(asked.workspace_id, 'member') then
    raise exception 'Only members can ask about a request' using errcode = '42501';
  end if;
  if asked.status <> 'open' then
    raise exception 'This request is %. Questions are asked while it''s open', asked.status
      using errcode = '23514';
  end if;
  if (select count(*) from public.questions where request_id = request) >= 100 then
    raise exception 'A request has at most 100 questions' using errcode = '54000';
  end if;
  insert into public.questions (workspace_id, request_id, text, asked_by, asked_by_agent)
  values (
    asked.workspace_id,
    request,
    btrim(ask_question.text),
    (select auth.uid()),
    private.agent_name()
  )
  returning id into made;
  return made;
end;
$$;

-- Answers a question, or changes its answer. Only a person answers, so an agent can't answer its
-- own questions.
create function public.answer_question(question uuid, answer text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  workspace uuid := (select workspace_id from public.questions where id = question);
begin
  if workspace is null or not access.holds(workspace, 'member') then
    raise exception 'Only members can answer a question' using errcode = '42501';
  end if;
  if private.by_agent() then
    raise exception 'An agent can''t answer a question. A person does that in Sulba'
      using errcode = '42501';
  end if;
  update public.questions
  set answer = btrim(answer_question.answer), answered_by = (select auth.uid()), answered_at = now()
  where id = question;
end;
$$;

-- Makes a spec with its first criteria, as before, and, for a spec drafted from a request, the
-- request it came from, which must be in the same workspace and not closed.
drop function public.create_spec(uuid, text, text[]);

create function public.create_spec(
  workspace uuid, title text, criteria text[] default '{}', request uuid default null
)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  given integer;
  made uuid;
  wording text;
  requested public.request_status;
begin
  if not access.holds(workspace, 'member') then
    raise exception 'Only members can write specs' using errcode = '42501';
  end if;
  if request is not null then
    select r.status into requested from public.requests r
    where r.id = request and r.workspace_id = workspace;
    if not found then
      raise exception 'There''s no such request in this workspace' using errcode = 'P0002';
    end if;
    if requested = 'closed' then
      raise exception 'This request is closed. Specs are drafted from open or planned requests'
        using errcode = '23514';
    end if;
  end if;
  if (select count(*) from public.specs where workspace_id = workspace) >= 1000 then
    raise exception 'A workspace can hold at most 1,000 specs' using errcode = '54000';
  end if;
  if coalesce(array_length(criteria, 1), 0) > 100 then
    raise exception 'A spec has at most 100 criteria' using errcode = '54000';
  end if;
  insert into private.spec_numbers (workspace_id, last) values (workspace, 1)
  on conflict (workspace_id) do update set last = private.spec_numbers.last + 1
  returning last into given;
  insert into public.specs (workspace_id, number, title, owner_id, created_by, request_id)
  values (workspace, given, btrim(create_spec.title), (select auth.uid()), (select auth.uid()), request)
  returning id into made;
  foreach wording in array criteria loop
    continue when btrim(wording) = '';
    perform public.add_criterion(made, wording);
  end loop;
  return given;
end;
$$;

revoke execute on function public.create_request(uuid, text, text) from public, anon;
revoke execute on function public.ask_question(uuid, text) from public, anon;
revoke execute on function public.answer_question(uuid, text) from public, anon;
revoke execute on function public.create_spec(uuid, text, text[], uuid) from public, anon;
grant execute on function public.create_request(uuid, text, text) to authenticated;
grant execute on function public.ask_question(uuid, text) to authenticated;
grant execute on function public.answer_question(uuid, text) to authenticated;
grant execute on function public.create_spec(uuid, text, text[], uuid) to authenticated;

-- Everyone in a workspace reads its requests and their questions; members and above change a
-- request. A request isn't deleted: it's closed, and keeps its number and history. Questions
-- change only through the functions above.
alter table public.requests enable row level security;
alter table public.questions enable row level security;

revoke all on public.requests, public.questions from anon, authenticated;
grant select on public.requests, public.questions to authenticated;
grant update (title, status, body) on public.requests to authenticated;

create policy "Members see their workspaces' requests" on public.requests
for select to authenticated using (workspace_id in (select access.workspace_ids()));

create policy "Members change requests" on public.requests
for update to authenticated
using (workspace_id in (select access.workspace_ids('member')))
with check (workspace_id in (select access.workspace_ids('member')));

create policy "Members see their workspaces' questions" on public.questions
for select to authenticated using (workspace_id in (select access.workspace_ids()));
