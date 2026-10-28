-- Coding agents work in a workspace through Sulba's MCP server, signed in with Supabase's OAuth
-- 2.1 server (decision record 51). An agent's token carries its OAuth client's ID, so Postgres
-- knows when an agent is acting. It acts for its person, within their role, on specs and their
-- criteria, until its person disconnects it; who is in a workspace, what it is called, its
-- repositories and the decisions about a spec stay with people, whether the agent asks through the
-- MCP server or calls the Data API.

-- Whether the request's token was issued to an OAuth client, that is, whether an agent is acting.
create function private.by_agent()
returns boolean
language sql
stable
set search_path = ''
as $$
  select (select auth.jwt()) ->> 'client_id' is not null
$$;

-- Whether the request is a person's, or an agent's that its person hasn't disconnected.
-- Disconnecting an agent ends its session at once, though its access token lasts until it
-- expires, so the workspaces it can reach go with the session.
create function private.connected()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select not private.by_agent() or exists (
    select from auth.sessions
    where id = ((select auth.jwt()) ->> 'session_id')::uuid and user_id = (select auth.uid())
  )
$$;

create or replace function access.workspace_ids(minimum public.workspace_role default 'viewer')
returns setof uuid
language sql
stable
security definer
set search_path = ''
as $$
  select workspace_id from public.members
  where person_id = (select auth.uid()) and role >= minimum and (select private.connected())
$$;

create or replace function access.holds(workspace uuid, minimum public.workspace_role)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select from public.members
    where workspace_id = workspace and person_id = (select auth.uid()) and role >= minimum
  ) and (select private.connected())
$$;

create or replace function access.coworker_ids()
returns setof uuid
language sql
stable
security definer
set search_path = ''
as $$
  select distinct theirs.person_id
  from public.members mine
  join public.members theirs on theirs.workspace_id = mine.workspace_id
  where mine.person_id = (select auth.uid()) and (select private.connected())
$$;

-- Refuses a change an agent makes, giving the trigger's argument as the reason.
create function private.refuse_agents()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if private.by_agent() then
    raise exception '%', tg_argv[0] using errcode = '42501';
  end if;
  return case when tg_op = 'DELETE' then old else new end;
end;
$$;

create trigger refuse_agents before insert or update or delete on public.workspaces
for each row execute function private.refuse_agents(
  'An agent can''t create, rename or delete a workspace. A person does that in Sulba'
);
create trigger refuse_agents before insert or update or delete on public.members
for each row execute function private.refuse_agents(
  'An agent can''t change who is in a workspace or their roles. A person does that in Sulba'
);
create trigger refuse_agents before insert or update or delete on public.invitations
for each row execute function private.refuse_agents(
  'An agent can''t invite people to a workspace. A person does that in Sulba'
);
create trigger refuse_agents before insert or update or delete on public.repositories
for each row execute function private.refuse_agents(
  'An agent can''t change a workspace''s repositories. An admin does that in Sulba'
);
create trigger refuse_agents before delete on auth.users
for each row execute function private.refuse_agents(
  'An agent can''t close an account. Its person does that in Sulba'
);
create trigger refuse_agents before delete on public.criteria
for each row execute function private.refuse_agents(
  'An agent can''t remove a criterion. A person does that in Sulba'
);

-- An agent drafts a spec, puts it in review and marks it implemented; a person approves,
-- abandons or supersedes it.
create function private.keep_decisions_with_people()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if private.by_agent()
    and new.status is distinct from old.status
    and new.status in ('approved', 'abandoned', 'superseded')
  then
    raise exception 'An agent can''t approve, abandon or supersede a spec. A person in the workspace does that'
      using errcode = '42501';
  end if;
  return new;
end;
$$;

create trigger keep_decisions_with_people before update of status on public.specs
for each row execute function private.keep_decisions_with_people();

-- Only a person confirms that a reworded criterion's tests check its new wording.
create function private.keep_confirmation_with_people()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if private.by_agent() and old.suspect_since is not null and new.suspect_since is null then
    raise exception 'An agent can''t confirm that a criterion''s tests check its wording. A person does that'
      using errcode = '42501';
  end if;
  return new;
end;
$$;

create trigger keep_confirmation_with_people before update of suspect_since on public.criteria
for each row execute function private.keep_confirmation_with_people();

revoke execute on function private.by_agent() from public;
revoke execute on function private.connected() from public;
revoke execute on function private.refuse_agents() from public;
revoke execute on function private.keep_decisions_with_people() from public;
revoke execute on function private.keep_confirmation_with_people() from public;

-- The agent's name, as its OAuth client gave it when it registered, so the history names each
-- agent that acted. It's kept with the change, as a log keeps what was true at the time.
alter table public.events add column actor_agent text;

create function private.name_agent()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.actor_client is not null then
    new.actor_agent := (
      select left(btrim(client_name), 64) from auth.oauth_clients where id::text = new.actor_client
    );
  end if;
  return new;
end;
$$;

revoke execute on function private.name_agent() from public;

create trigger name_agent before insert on public.events
for each row execute function private.name_agent();

-- The app's consent page for agents is at /app/oauth/consent, so no workspace can take that
-- address.
alter table public.workspaces drop constraint workspaces_slug_check;
alter table public.workspaces add constraint workspaces_slug_check check (
  slug ~ '^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$'
  and slug !~ '--'
  and slug not in (
    'account', 'admin', 'api', 'app', 'assets', 'docs', 'help', 'join', 'login', 'logout', 'new',
    'oauth', 'settings', 'sign-in', 'sign-out', 'static'
  )
);
