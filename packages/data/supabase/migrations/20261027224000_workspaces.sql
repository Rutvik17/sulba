-- Workspaces: a team's space in the app, the people in it and what each may do, the links that
-- invite people in, and the log of every change to them (decision record 48). Every row belongs to
-- one workspace, and only its members can read it.

-- What a member may do, from least to most: a viewer reads, a member also writes, an admin also
-- manages people and settings, and an owner also manages owners and can delete the workspace.
-- Comparisons follow this order.
create type public.workspace_role as enum ('viewer', 'member', 'admin', 'owner');

-- Who made a change: a person in the browser, an agent on a person's behalf, GitHub, or the
-- database itself.
create type public.actor_kind as enum ('person', 'agent', 'github', 'system');

-- Each person as their workspaces show them: the name and email address their sign-in gave. Kept
-- in step with auth.users, which the Data API doesn't serve.
create table public.people (
  id uuid primary key references auth.users (id) on delete cascade,
  name text not null default '',
  email text,
  updated_at timestamptz not null default now()
);

create function private.copy_person()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.people (id, name, email)
  values (
    new.id,
    left(btrim(coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name', '')), 128),
    new.email
  )
  on conflict (id) do update
    set name = excluded.name, email = excluded.email, updated_at = now();
  return new;
end;
$$;

create trigger copy_person
after insert or update of email, raw_user_meta_data on auth.users
for each row execute function private.copy_person();

revoke execute on function private.copy_person() from public;

insert into public.people (id, name, email)
select
  id,
  left(btrim(coalesce(raw_user_meta_data ->> 'full_name', raw_user_meta_data ->> 'name', '')), 128),
  email
from auth.users;

create table public.workspaces (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(name) between 1 and 64 and name = btrim(name)),
  -- The workspace's address, sulba.dev/app/<slug>: 3 to 32 lowercase letters, digits and single
  -- hyphens, and none of the app's own addresses.
  slug text not null unique check (
    slug ~ '^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$'
    and slug !~ '--'
    and slug not in (
      'account', 'admin', 'api', 'app', 'assets', 'docs', 'help', 'join', 'login', 'logout', 'new',
      'settings', 'sign-in', 'sign-out', 'static'
    )
  ),
  created_at timestamptz not null default now()
);

create table public.members (
  workspace_id uuid not null references public.workspaces (id) on delete cascade,
  person_id uuid not null references public.people (id) on delete cascade,
  role public.workspace_role not null,
  joined_at timestamptz not null default now(),
  primary key (workspace_id, person_id)
);

-- Serves every policy below, which asks which workspaces the signed-in person is in.
create index members_by_person on public.members (person_id);

-- A link that lets whoever opens it join as a viewer or a member, until it expires or an admin
-- revokes it. Only the token's hash is kept: the token itself is in the link alone.
create table public.invitations (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces (id) on delete cascade,
  role public.workspace_role not null check (role in ('viewer', 'member')),
  token_hash bytea not null unique,
  created_by uuid references public.people (id) on delete set null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '7 days'
);

create index invitations_by_workspace on public.invitations (workspace_id);

-- Every change to a workspace's rows, in order, written by the database in the same transaction
-- as the change, so no way of writing can skip it. Its id orders the changes.
create table public.events (
  id bigint generated always as identity primary key,
  workspace_id uuid not null references public.workspaces (id) on delete cascade,
  at timestamptz not null default now(),
  actor_kind public.actor_kind not null,
  -- The person who acted, or for whom an agent acted.
  actor_id uuid references public.people (id) on delete set null,
  -- The agent's OAuth client, when an agent acted.
  actor_client text,
  -- What happened, such as 'member.updated'.
  action text not null,
  subject_type text not null,
  subject_id text not null,
  -- Each field that changed, as [before, after].
  changes jsonb not null default '{}'
);

create index events_by_workspace on public.events (workspace_id, id);
create index events_by_subject on public.events (workspace_id, subject_type, subject_id, id);

-- What the row-level policies below ask about the signed-in person. Signed-in people can use
-- these functions, so policies can call them, but the Data API doesn't serve the schema.
create schema access;

-- The workspaces the signed-in person is in with `minimum` or a higher role. Policies read
-- it once a statement, as its owner, so they don't run the members table's own policy per row.
create function access.workspace_ids(minimum public.workspace_role default 'viewer')
returns setof uuid
language sql
stable
security definer
set search_path = ''
as $$
  select workspace_id from public.members
  where person_id = (select auth.uid()) and role >= minimum
$$;

-- Whether the signed-in person holds `minimum` or a higher role in the workspace.
create function access.holds(workspace uuid, minimum public.workspace_role)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select from public.members
    where workspace_id = workspace and person_id = (select auth.uid()) and role >= minimum
  )
$$;

-- The people who share a workspace with the signed-in person.
create function access.coworker_ids()
returns setof uuid
language sql
stable
security definer
set search_path = ''
as $$
  select distinct theirs.person_id
  from public.members mine
  join public.members theirs on theirs.workspace_id = mine.workspace_id
  where mine.person_id = (select auth.uid())
$$;

revoke execute on function access.workspace_ids(public.workspace_role) from public;
revoke execute on function access.holds(uuid, public.workspace_role) from public;
revoke execute on function access.coworker_ids() from public;
grant usage on schema access to authenticated;
grant execute on function access.workspace_ids(public.workspace_role) to authenticated;
grant execute on function access.holds(uuid, public.workspace_role) to authenticated;
grant execute on function access.coworker_ids() to authenticated;

-- Writes a row's change to the events table. Its arguments name the kind of subject and the
-- column that identifies it; columns listed after them are left out of the log.
create function private.record_event()
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
  workspace uuid := coalesce(after, before) ->> case when subject = 'workspace' then 'id' else 'workspace_id' end;
  client text := (select auth.jwt()) ->> 'client_id';
  -- The person who acted, unless this change is their account being closed, which has already
  -- removed them.
  actor uuid := (select id from public.people where id = (select auth.uid()));
  changed jsonb := '{}';
  field text;
begin
  -- A workspace being deleted takes its log with it.
  if not exists (select from public.workspaces where id = workspace) then
    return null;
  end if;
  for field in select jsonb_object_keys(coalesce(after, before)) loop
    continue when field = any (hidden) or field = 'updated_at';
    if before -> field is distinct from after -> field then
      changed := changed || jsonb_build_object(
        field,
        jsonb_build_array(coalesce(before -> field, 'null'::jsonb), coalesce(after -> field, 'null'::jsonb))
      );
    end if;
  end loop;
  insert into public.events (
    workspace_id, actor_kind, actor_id, actor_client, action, subject_type, subject_id, changes
  )
  values (
    workspace,
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
    coalesce(after, before) ->> key,
    changed
  );
  return null;
end;
$$;

revoke execute on function private.record_event() from public;

create trigger record_event after insert or update or delete on public.workspaces
for each row execute function private.record_event('workspace', 'id');
create trigger record_event after insert or update or delete on public.members
for each row execute function private.record_event('member', 'person_id');
create trigger record_event after insert or update or delete on public.invitations
for each row execute function private.record_event('invitation', 'id', 'token_hash');

-- Makes a workspace with the signed-in person as its owner. Past 10 workspaces that a person
-- owns, more are refused, so one account can't fill the database.
create function public.create_workspace(name text, slug text)
returns public.workspaces
language plpgsql
security definer
set search_path = ''
as $$
declare
  made public.workspaces;
begin
  if (select auth.uid()) is null then
    raise exception 'Sign in to create a workspace' using errcode = '42501';
  end if;
  if (
    select count(*) from public.members where person_id = (select auth.uid()) and role = 'owner'
  ) >= 10 then
    raise exception 'A person can own at most 10 workspaces' using errcode = '54000';
  end if;
  insert into public.workspaces (name, slug)
  values (btrim(create_workspace.name), lower(btrim(create_workspace.slug)))
  returning * into made;
  insert into public.members (workspace_id, person_id, role)
  values (made.id, (select auth.uid()), 'owner');
  return made;
end;
$$;

-- Makes an invitation link's token, which only this call ever sees. An admin can have 50 links
-- open in a workspace at once.
create function public.create_invitation(workspace uuid, role public.workspace_role)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  token text := replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', '');
begin
  if not access.holds(workspace, 'admin') then
    raise exception 'Only admins can invite people' using errcode = '42501';
  end if;
  if (
    select count(*) from public.invitations
    where workspace_id = workspace and expires_at > now()
  ) >= 50 then
    raise exception 'A workspace can have at most 50 open invitations' using errcode = '54000';
  end if;
  insert into public.invitations (workspace_id, role, token_hash, created_by)
  values (workspace, create_invitation.role, sha256(convert_to(token, 'UTF8')), (select auth.uid()));
  return token;
end;
$$;

-- What an invitation link offers, for the page that asks whether to join: the workspace's name
-- and the role. Nothing when the link has expired or been revoked.
create function public.invitation(token text)
returns table (workspace_name text, role public.workspace_role)
language sql
stable
security definer
set search_path = ''
as $$
  select w.name, i.role
  from public.invitations i
  join public.workspaces w on w.id = i.workspace_id
  where i.token_hash = sha256(convert_to(token, 'UTF8')) and i.expires_at > now()
$$;

-- Joins the signed-in person to the workspace an invitation link is for, and gives the
-- workspace's address. Someone already in it keeps the role they have.
create function public.accept_invitation(token text)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  offered public.invitations;
begin
  if (select auth.uid()) is null then
    raise exception 'Sign in to join a workspace' using errcode = '42501';
  end if;
  select * into offered from public.invitations
  where token_hash = sha256(convert_to(token, 'UTF8')) and expires_at > now();
  if not found then
    raise exception 'This invitation has expired or been revoked' using errcode = 'P0002';
  end if;
  insert into public.members (workspace_id, person_id, role)
  values (offered.workspace_id, (select auth.uid()), offered.role)
  on conflict (workspace_id, person_id) do nothing;
  return (select slug from public.workspaces where id = offered.workspace_id);
end;
$$;

-- Refuses a change that would leave a workspace with no owner.
create function private.keep_an_owner(workspace uuid, person uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if (
    select role from public.members where workspace_id = workspace and person_id = person
  ) = 'owner' and (
    select count(*) from public.members where workspace_id = workspace and role = 'owner'
  ) = 1 then
    raise exception 'A workspace needs an owner: make someone else an owner first'
      using errcode = '23514';
  end if;
end;
$$;

revoke execute on function private.keep_an_owner(uuid, uuid) from public;

-- Changes a member's role. Admins change viewers, members and admins; only owners make or unmake
-- owners.
create function public.set_member_role(workspace uuid, person uuid, role public.workspace_role)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  held public.workspace_role;
begin
  select m.role into held from public.members m
  where m.workspace_id = workspace and m.person_id = person;
  if not found then
    raise exception 'They aren''t a member of this workspace' using errcode = 'P0002';
  end if;
  if not access.holds(
    workspace,
    case when 'owner' in (held, set_member_role.role) then 'owner' else 'admin' end::public.workspace_role
  ) then
    raise exception 'Only admins change roles, and only owners change owners' using errcode = '42501';
  end if;
  if set_member_role.role <> 'owner' then
    perform private.keep_an_owner(workspace, person);
  end if;
  update public.members m set role = set_member_role.role
  where m.workspace_id = workspace and m.person_id = person and m.role <> set_member_role.role;
end;
$$;

-- Removes a member, or lets a person leave. Admins remove viewers, members and admins; only
-- owners remove owners.
create function public.remove_member(workspace uuid, person uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  held public.workspace_role;
begin
  select role into held from public.members
  where workspace_id = workspace and person_id = person;
  if not found then
    raise exception 'They aren''t a member of this workspace' using errcode = 'P0002';
  end if;
  if person <> (select auth.uid())
    and not access.holds(
      workspace, case when held = 'owner' then 'owner' else 'admin' end::public.workspace_role
    )
  then
    raise exception 'Only admins remove people, and only owners remove owners' using errcode = '42501';
  end if;
  perform private.keep_an_owner(workspace, person);
  delete from public.members where workspace_id = workspace and person_id = person;
end;
$$;

-- Deletes a workspace and everything in it. Owners only.
create function public.delete_workspace(workspace uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not access.holds(workspace, 'owner') then
    raise exception 'Only owners can delete a workspace' using errcode = '42501';
  end if;
  delete from public.workspaces where id = workspace;
end;
$$;

revoke execute on function public.create_workspace(text, text) from public, anon;
revoke execute on function public.create_invitation(uuid, public.workspace_role) from public, anon;
revoke execute on function public.invitation(text) from public;
revoke execute on function public.accept_invitation(text) from public, anon;
revoke execute on function public.set_member_role(uuid, uuid, public.workspace_role) from public, anon;
revoke execute on function public.remove_member(uuid, uuid) from public, anon;
revoke execute on function public.delete_workspace(uuid) from public, anon;
grant execute on function public.create_workspace(text, text) to authenticated;
grant execute on function public.create_invitation(uuid, public.workspace_role) to authenticated;
-- Visitors see what a link offers before they sign in to accept it.
grant execute on function public.invitation(text) to anon, authenticated;
grant execute on function public.accept_invitation(text) to authenticated;
grant execute on function public.set_member_role(uuid, uuid, public.workspace_role) to authenticated;
grant execute on function public.remove_member(uuid, uuid) to authenticated;
grant execute on function public.delete_workspace(uuid) to authenticated;

-- Closing an account first deletes the workspaces where the person is the only member, and is
-- refused while they are the only owner of one that has others in it.
create or replace function public.close_account()
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if exists (
    select from public.members m
    where m.person_id = (select auth.uid()) and m.role = 'owner'
      and not exists (
        select from public.members o
        where o.workspace_id = m.workspace_id and o.role = 'owner' and o.person_id <> m.person_id
      )
      and exists (
        select from public.members o
        where o.workspace_id = m.workspace_id and o.person_id <> m.person_id
      )
  ) then
    raise exception 'Make someone else an owner of each workspace you own first'
      using errcode = '23514';
  end if;
  delete from public.workspaces w
  where exists (select from public.members m where m.workspace_id = w.id and m.person_id = (select auth.uid()))
    and not exists (select from public.members m where m.workspace_id = w.id and m.person_id <> (select auth.uid()));
  delete from auth.users where id = (select auth.uid());
end;
$$;

-- Only signed-in people reach these tables, and only the rows of their own workspaces. Changes
-- to members and invitations go through the functions above; admins rename a workspace and
-- revoke its links directly.
alter table public.people enable row level security;
alter table public.workspaces enable row level security;
alter table public.members enable row level security;
alter table public.invitations enable row level security;
alter table public.events enable row level security;

revoke all on public.people, public.workspaces, public.members, public.invitations, public.events
from anon, authenticated;
grant select on public.people, public.workspaces, public.members, public.events to authenticated;
grant update (name) on public.workspaces to authenticated;
grant select (id, workspace_id, role, created_by, created_at, expires_at) on public.invitations
to authenticated;
grant delete on public.invitations to authenticated;

create policy "People see themselves and the people they work with" on public.people
for select to authenticated
using (id = (select auth.uid()) or id in (select access.coworker_ids()));

create policy "Members see their workspaces" on public.workspaces
for select to authenticated using (id in (select access.workspace_ids()));

create policy "Admins rename their workspaces" on public.workspaces
for update to authenticated
using (id in (select access.workspace_ids('admin')))
with check (id in (select access.workspace_ids('admin')));

create policy "Members see who is in their workspaces" on public.members
for select to authenticated using (workspace_id in (select access.workspace_ids()));

create policy "Admins see their workspaces' invitations" on public.invitations
for select to authenticated using (workspace_id in (select access.workspace_ids('admin')));

create policy "Admins revoke invitations" on public.invitations
for delete to authenticated using (workspace_id in (select access.workspace_ids('admin')));

create policy "Members see their workspaces' history" on public.events
for select to authenticated using (workspace_id in (select access.workspace_ids()));
