-- Releases: a request delivered once every spec drafted from it is approved and every one of their
-- criteria is proven by the workspace's tests, with a person approving it (decision record 62).
-- Each release keeps what was proven when it was approved, so its document says what the person
-- agreed to even after the specs or the tests change. Agents can't approve a release.

create table public.releases (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null,
  request_id uuid not null,
  number integer not null check (number > 0),
  note text check (note is null or (char_length(note) between 1 and 2000 and note = btrim(note))),
  -- The request's specs, each criterion with the tests that proved it, and the tasks that built
  -- them, as they stood when the release was approved.
  snapshot jsonb not null,
  approved_by uuid references public.people (id) on delete set null,
  approved_at timestamptz not null default now(),
  unique (request_id, number),
  foreign key (workspace_id, request_id) references public.requests (workspace_id, id) on delete cascade
);

create index releases_by_workspace on public.releases (workspace_id);

-- The last number given to each request's releases.
create table private.release_numbers (
  request_id uuid primary key references public.requests (id) on delete cascade,
  last integer not null
);

alter table private.release_numbers enable row level security;

create trigger record_event after insert or update or delete on public.releases
for each row execute function private.record_event('release', 'id', 'snapshot');

-- Approves a release of a request and gives its number. A member approves it once every spec
-- drafted from the request, other than those abandoned or superseded, is approved or implemented,
-- has criteria, and has every criterion proven.
create function public.approve_release(request uuid, note text default null)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  found_request public.requests;
  unready text;
  made jsonb;
  given integer;
begin
  select * into found_request from public.requests where id = request;
  if not found or not access.holds(found_request.workspace_id, 'member') then
    raise exception 'Only members can approve a release' using errcode = '42501';
  end if;
  if private.by_agent() then
    raise exception 'An agent can''t approve a release. A person does that in Sulba'
      using errcode = '42501';
  end if;
  if found_request.status = 'closed' then
    raise exception 'This request is closed, so it has nothing to release' using errcode = '23514';
  end if;
  if not exists (
    select from public.specs s
    where s.request_id = request and s.status not in ('abandoned', 'superseded')
  ) then
    raise exception 'No spec has been drafted from this request yet' using errcode = '23514';
  end if;
  select format('SPEC-%s is %s', s.number, replace(s.status::text, '_', ' ')) into unready
  from public.specs s
  where s.request_id = request and s.status in ('draft', 'in_review')
  order by s.number
  limit 1;
  if unready is not null then
    raise exception '%. Every spec is approved before its release', unready using errcode = '23514';
  end if;
  select format('SPEC-%s has no criteria', s.number) into unready
  from public.specs s
  where s.request_id = request and s.status in ('approved', 'implemented')
    and not exists (select from public.criteria c where c.spec_id = s.id)
  order by s.number
  limit 1;
  if unready is null then
    select format('SPEC-%s/AC-%s isn''t proven', p.spec_number, p.criterion_number) into unready
    from public.criterion_proofs p
    join public.specs s on s.id = p.spec_id
    where s.request_id = request and s.status in ('approved', 'implemented') and p.state <> 'proven'
    order by p.spec_number, p.criterion_number
    limit 1;
  end if;
  if unready is not null then
    raise exception '%. Every criterion is proven by the tests before its release', unready
      using errcode = '23514';
  end if;

  select jsonb_agg(
    jsonb_build_object(
      'number', s.number,
      'title', s.title,
      'status', s.status,
      'criteria', (
        select jsonb_agg(
          jsonb_build_object('number', p.criterion_number, 'text', p.text, 'tests', p.tests)
          order by p.criterion_number
        )
        from public.criterion_proofs p
        where p.spec_id = s.id
      ),
      'tasks', (
        select coalesce(
          jsonb_agg(
            jsonb_build_object(
              'number', t.number, 'title', t.title, 'role', t.role, 'status', t.status,
              'pull_request', t.pull_request
            )
            order by t.number
          ),
          '[]'::jsonb
        )
        from public.tasks t
        where t.spec_id = s.id and t.status <> 'canceled'
      )
    )
    order by s.number
  ) into made
  from public.specs s
  where s.request_id = request and s.status in ('approved', 'implemented');

  insert into private.release_numbers (request_id, last) values (request, 1)
  on conflict (request_id) do update set last = private.release_numbers.last + 1
  returning last into given;
  insert into public.releases (workspace_id, request_id, number, note, snapshot, approved_by)
  values (
    found_request.workspace_id, request, given, nullif(btrim(approve_release.note), ''), made,
    (select auth.uid())
  );
  return given;
end;
$$;

revoke execute on function public.approve_release(uuid, text) from public, anon;
grant execute on function public.approve_release(uuid, text) to authenticated;

-- Everyone in a workspace reads its releases. A release changes only by being approved, and is
-- never edited or deleted.
alter table public.releases enable row level security;

revoke all on public.releases from anon, authenticated;
grant select on public.releases to authenticated;

create policy "Members see their workspaces' releases" on public.releases
for select to authenticated using (workspace_id in (select access.workspace_ids()));
