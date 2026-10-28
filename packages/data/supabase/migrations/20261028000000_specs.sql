-- Specs, each with the acceptance criteria that say when it's done (decision record 49). Each has
-- a number in its workspace, SPEC-12, and each criterion a number in its spec, SPEC-12/AC-3. A
-- number is never given twice, so an ID in a test's name, a branch or a commit always means the
-- same thing.

create type public.spec_status as enum (
  'draft', 'in_review', 'approved', 'implemented', 'abandoned', 'superseded'
);

create table public.specs (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces (id) on delete cascade,
  number integer not null check (number > 0),
  title text not null check (char_length(title) between 1 and 200 and title = btrim(title)),
  status public.spec_status not null default 'draft',
  -- Markdown: summary, context, goals, design and the rest, as the team writes them.
  body text not null default '' check (char_length(body) <= 50000),
  owner_id uuid references public.people (id) on delete set null,
  created_by uuid references public.people (id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workspace_id, number),
  unique (workspace_id, id)
);

create table public.criteria (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null,
  spec_id uuid not null,
  number integer not null check (number > 0),
  text text not null check (char_length(text) between 1 and 1000 and text = btrim(text)),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key (workspace_id, spec_id) references public.specs (workspace_id, id) on delete cascade,
  unique (spec_id, number)
);

create index criteria_by_workspace on public.criteria (workspace_id);

-- The last number given in each workspace and each spec, so a deleted criterion's number isn't
-- given again. Only the functions below read and write them.
create table private.spec_numbers (
  workspace_id uuid primary key references public.workspaces (id) on delete cascade,
  last integer not null
);

create table private.criterion_numbers (
  spec_id uuid primary key references public.specs (id) on delete cascade,
  last integer not null
);

alter table private.spec_numbers enable row level security;
alter table private.criterion_numbers enable row level security;

-- The spec a change belongs to, for a spec's own changes and its criteria's, so a spec's page
-- reads its history in one request.
alter table public.events add column spec_id uuid;
create index events_by_spec on public.events (workspace_id, spec_id, id) where spec_id is not null;

-- Writes a row's change to the events table, as before, with three changes. A field left out of
-- the log, such as a secret or a spec's whole text, appears with null when it changed, so the log
-- says it changed without keeping it. An update that changes nothing is left out. And edits of
-- those fields alone by the same person within 10 minutes of their last count as one, so saving
-- a spec as it's written doesn't fill its history.
create or replace function private.record_event()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  subject text := tg_argv[0];
  key text := tg_argv[1];
  hidden text[] := tg_argv[2:];
  before jsonb := case when tg_op <> 'INSERT' then to_jsonb(old) end;
  after jsonb := case when tg_op <> 'DELETE' then to_jsonb(new) end;
  item jsonb := coalesce(after, before);
  workspace uuid := item ->> case when subject = 'workspace' then 'id' else 'workspace_id' end;
  spec uuid := case when subject = 'spec' then (item ->> 'id')::uuid else (item ->> 'spec_id')::uuid end;
  client text := (select auth.jwt()) ->> 'client_id';
  -- The person who acted, unless this change is their account being closed, which has already
  -- removed them.
  actor uuid := (select id from public.people where id = (select auth.uid()));
  changed jsonb := '{}';
  field text;
  latest public.events;
begin
  -- A workspace being deleted takes its log with it.
  if not exists (select from public.workspaces where id = workspace) then
    return null;
  end if;
  for field in select jsonb_object_keys(item) loop
    continue when field = 'updated_at';
    if before -> field is distinct from after -> field then
      changed := changed || jsonb_build_object(
        field,
        case
          when field = any (hidden) then 'null'::jsonb
          else jsonb_build_array(coalesce(before -> field, 'null'::jsonb), coalesce(after -> field, 'null'::jsonb))
        end
      );
    end if;
  end loop;
  if tg_op = 'UPDATE' then
    if changed = '{}' then
      return null;
    end if;
    if not exists (select from jsonb_each(changed) where value <> 'null'::jsonb) then
      select * into latest from public.events
      where workspace_id = workspace and subject_type = subject and subject_id = item ->> key
      order by id desc
      limit 1;
      if latest.action = subject || '.updated' and latest.actor_id is not distinct from actor
        and latest.changes = changed and latest.at > now() - interval '10 minutes' then
        return null;
      end if;
    end if;
  end if;
  insert into public.events (
    workspace_id, spec_id, actor_kind, actor_id, actor_client, action, subject_type, subject_id, changes
  )
  values (
    workspace,
    spec,
    case
      when nullif(current_setting('sulba.actor_kind', true), '') is not null
        then current_setting('sulba.actor_kind', true)::public.actor_kind
      when client is not null then 'agent'
      when (select auth.uid()) is not null then 'person'
      else 'system'
    end,
    actor,
    client,
    subject || case tg_op when 'INSERT' then '.created' when 'UPDATE' then '.updated' else '.deleted' end,
    subject,
    item ->> key,
    changed
  );
  return null;
end;
$$;

create trigger record_event after insert or update or delete on public.specs
for each row execute function private.record_event('spec', 'id', 'body');
create trigger record_event after insert or update or delete on public.criteria
for each row execute function private.record_event('criterion', 'id');

-- Keeps each row's updated_at.
create function private.touch()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

revoke execute on function private.touch() from public;

create trigger touch before update on public.specs
for each row execute function private.touch();
create trigger touch before update on public.criteria
for each row execute function private.touch();

-- A spec's owner is one of its workspace's members. Someone who leaves stops owning its specs.
create function private.check_owner()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.owner_id is not null and not exists (
    select from public.members where workspace_id = new.workspace_id and person_id = new.owner_id
  ) then
    raise exception 'A spec''s owner is one of the workspace''s members' using errcode = '23514';
  end if;
  return new;
end;
$$;

revoke execute on function private.check_owner() from public;

create trigger check_owner before insert or update of owner_id on public.specs
for each row execute function private.check_owner();

create function private.disown()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.specs set owner_id = null
  where workspace_id = old.workspace_id and owner_id = old.person_id;
  return null;
end;
$$;

revoke execute on function private.disown() from public;

create trigger disown after delete on public.members
for each row execute function private.disown();

-- Makes a spec with its first criteria, and gives its number. Its maker owns it. Members and
-- above write specs; a workspace holds at most 1,000.
create function public.create_spec(workspace uuid, title text, criteria text[] default '{}')
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  given integer;
  made uuid;
  wording text;
begin
  if not access.holds(workspace, 'member') then
    raise exception 'Only members can write specs' using errcode = '42501';
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
  insert into public.specs (workspace_id, number, title, owner_id, created_by)
  values (workspace, given, btrim(create_spec.title), (select auth.uid()), (select auth.uid()))
  returning id into made;
  foreach wording in array criteria loop
    continue when btrim(wording) = '';
    perform public.add_criterion(made, wording);
  end loop;
  return given;
end;
$$;

-- Adds a criterion to the end of a spec, and gives its number. A spec has at most 100.
create function public.add_criterion(spec uuid, text text)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  workspace uuid := (select workspace_id from public.specs where id = spec);
  given integer;
begin
  if workspace is null or not access.holds(workspace, 'member') then
    raise exception 'Only members can write specs' using errcode = '42501';
  end if;
  if (select count(*) from public.criteria where spec_id = spec) >= 100 then
    raise exception 'A spec has at most 100 criteria' using errcode = '54000';
  end if;
  insert into private.criterion_numbers (spec_id, last) values (spec, 1)
  on conflict (spec_id) do update set last = private.criterion_numbers.last + 1
  returning last into given;
  insert into public.criteria (workspace_id, spec_id, number, text)
  values (workspace, spec, given, btrim(add_criterion.text));
  return given;
end;
$$;

revoke execute on function public.create_spec(uuid, text, text[]) from public, anon;
revoke execute on function public.add_criterion(uuid, text) from public, anon;
grant execute on function public.create_spec(uuid, text, text[]) to authenticated;
grant execute on function public.add_criterion(uuid, text) to authenticated;

-- Everyone in a workspace reads its specs; members and above change them. A spec isn't deleted:
-- it's abandoned or superseded, and keeps its number and history.
alter table public.specs enable row level security;
alter table public.criteria enable row level security;

revoke all on public.specs, public.criteria from anon, authenticated;
grant select on public.specs, public.criteria to authenticated;
grant update (title, status, body, owner_id) on public.specs to authenticated;
grant update (text) on public.criteria to authenticated;
grant delete on public.criteria to authenticated;

create policy "Members see their workspaces' specs" on public.specs
for select to authenticated using (workspace_id in (select access.workspace_ids()));

create policy "Members change specs" on public.specs
for update to authenticated
using (workspace_id in (select access.workspace_ids('member')))
with check (workspace_id in (select access.workspace_ids('member')));

create policy "Members see their workspaces' criteria" on public.criteria
for select to authenticated using (workspace_id in (select access.workspace_ids()));

create policy "Members reword criteria" on public.criteria
for update to authenticated
using (workspace_id in (select access.workspace_ids('member')))
with check (workspace_id in (select access.workspace_ids('member')));

create policy "Members remove criteria" on public.criteria
for delete to authenticated using (workspace_id in (select access.workspace_ids('member')));
