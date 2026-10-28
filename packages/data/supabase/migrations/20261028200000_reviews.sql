-- A spec's reviewers and what each of them answered (decision record 52). A workspace's members
-- name a spec's reviewers, who can be anyone in the workspace but its owner. A spec with reviewers
-- is approved when the last of them approves it, and not before. A change to its title, text or
-- criteria while it's in review asks those who had approved it to review it again, so every
-- approval is of the same spec; a reviewer who asked for changes keeps that answer until they
-- answer again.

create type public.review_verdict as enum ('pending', 'approved', 'changes_requested');

create table public.spec_reviews (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null,
  spec_id uuid not null,
  reviewer_id uuid not null references public.people (id) on delete cascade,
  requested_by uuid references public.people (id) on delete set null,
  requested_at timestamptz not null default now(),
  verdict public.review_verdict not null default 'pending',
  -- What the reviewer said with their answer; asking for changes needs it.
  note text check (char_length(note) between 1 and 2000 and note = btrim(note)),
  answered_at timestamptz,
  foreign key (workspace_id, spec_id) references public.specs (workspace_id, id) on delete cascade,
  unique (spec_id, reviewer_id),
  check (verdict <> 'changes_requested' or note is not null)
);

create index spec_reviews_by_reviewer on public.spec_reviews (workspace_id, reviewer_id, verdict);

create trigger record_event after insert or update or delete on public.spec_reviews
for each row execute function private.record_event('review', 'id');

-- Someone who leaves a workspace stops reviewing its specs.
create function private.leave_reviews()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  delete from public.spec_reviews
  where workspace_id = old.workspace_id and reviewer_id = old.person_id;
  return null;
end;
$$;

revoke execute on function private.leave_reviews() from public;

create trigger leave_reviews after delete on public.members
for each row execute function private.leave_reviews();

-- Asks the spec's reviewers who had approved it to review it again.
create function private.ask_again(spec uuid)
returns void
language sql
security definer
set search_path = ''
as $$
  update public.spec_reviews
  set verdict = 'pending', note = null, answered_at = null
  where spec_id = spec and verdict = 'approved'
$$;

revoke execute on function private.ask_again(uuid) from public;

-- A spec with reviewers is approved only once every one of them has; one that goes into review
-- again starts a new round, and one in review that changes asks its approvers again. A reviewer
-- who comes to own the spec stops reviewing it.
create function private.keep_reviews_current()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.status = 'approved' and old.status is distinct from 'approved' and exists (
    select from public.spec_reviews where spec_id = new.id and verdict <> 'approved'
  ) then
    raise exception 'Every reviewer has to approve the spec first' using errcode = '23514';
  end if;
  if new.owner_id is distinct from old.owner_id then
    delete from public.spec_reviews where spec_id = new.id and reviewer_id = new.owner_id;
  end if;
  if new.status = 'in_review' and old.status is distinct from 'in_review' then
    perform private.ask_again(new.id);
  elsif new.status = 'in_review'
    and (new.title is distinct from old.title or new.body is distinct from old.body) then
    perform private.ask_again(new.id);
  end if;
  return null;
end;
$$;

revoke execute on function private.keep_reviews_current() from public;

create trigger keep_reviews_current after update of status, title, body, owner_id on public.specs
for each row execute function private.keep_reviews_current();

-- A change to a spec's criteria is a change to the spec: it's when the spec was last updated, and
-- while it's in review it asks its approvers again.
create function private.criteria_changed()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  spec uuid := coalesce(new.spec_id, old.spec_id);
begin
  if tg_op = 'UPDATE' and new.text is not distinct from old.text then
    return null;
  end if;
  update public.specs set updated_at = now() where id = spec;
  if exists (select from public.specs where id = spec and status = 'in_review') then
    perform private.ask_again(spec);
  end if;
  return null;
end;
$$;

revoke execute on function private.criteria_changed() from public;

create trigger criteria_changed after insert or update or delete on public.criteria
for each row execute function private.criteria_changed();

-- Names a reviewer for a spec, or asks one again. Members and above choose reviewers, up to 10
-- a spec, from the workspace's people, and a spec's owner doesn't review it. A spec that's been
-- approved, implemented, abandoned or superseded takes no more reviewers.
create function public.request_review(spec uuid, reviewer uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  target public.specs;
begin
  select * into target from public.specs where id = spec;
  if private.by_agent() then
    raise exception 'An agent can''t choose a spec''s reviewers. A person does that in Sulba'
      using errcode = '42501';
  end if;
  if target.id is null or not access.holds(target.workspace_id, 'member') then
    raise exception 'Only members can choose a spec''s reviewers' using errcode = '42501';
  end if;
  if target.status not in ('draft', 'in_review') then
    raise exception 'Only a draft or a spec in review takes reviewers' using errcode = '23514';
  end if;
  if not exists (
    select from public.members where workspace_id = target.workspace_id and person_id = reviewer
  ) then
    raise exception 'A reviewer is one of the workspace''s people' using errcode = '23514';
  end if;
  if reviewer = target.owner_id then
    raise exception 'A spec''s owner doesn''t review it' using errcode = '23514';
  end if;
  if not exists (select from public.spec_reviews where spec_id = spec and reviewer_id = reviewer)
    and (select count(*) from public.spec_reviews where spec_id = spec) >= 10 then
    raise exception 'A spec has at most 10 reviewers' using errcode = '54000';
  end if;
  insert into public.spec_reviews (workspace_id, spec_id, reviewer_id, requested_by)
  values (target.workspace_id, spec, reviewer, (select auth.uid()))
  on conflict (spec_id, reviewer_id) do update
  set verdict = 'pending', note = null, answered_at = null, requested_by = excluded.requested_by,
    requested_at = now()
  where public.spec_reviews.verdict <> 'pending';
end;
$$;

-- Takes a reviewer off a spec.
create function public.remove_reviewer(spec uuid, reviewer uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  workspace uuid := (select workspace_id from public.specs where id = spec);
begin
  if private.by_agent() then
    raise exception 'An agent can''t choose a spec''s reviewers. A person does that in Sulba'
      using errcode = '42501';
  end if;
  if workspace is null or not access.holds(workspace, 'member') then
    raise exception 'Only members can choose a spec''s reviewers' using errcode = '42501';
  end if;
  delete from public.spec_reviews where spec_id = spec and reviewer_id = reviewer;
end;
$$;

-- A reviewer's answer: approved, or changes requested with what to change. The last approval
-- approves the spec. Returns the spec's status.
create function public.review_spec(
  spec uuid,
  verdict public.review_verdict,
  note text default null
)
returns public.spec_status
language plpgsql
security definer
set search_path = ''
as $$
declare
  target public.specs;
  said text := nullif(btrim(coalesce(review_spec.note, '')), '');
begin
  select * into target from public.specs where id = spec;
  if private.by_agent() then
    raise exception 'An agent can''t review a spec. A person does that in Sulba'
      using errcode = '42501';
  end if;
  if target.id is null or not exists (
    select from public.spec_reviews where spec_id = spec and reviewer_id = (select auth.uid())
  ) then
    raise exception 'Only the spec''s reviewers can review it' using errcode = '42501';
  end if;
  if target.status <> 'in_review' then
    raise exception 'Only a spec in review can be reviewed' using errcode = '23514';
  end if;
  if review_spec.verdict = 'pending' then
    raise exception 'A review approves the spec or asks for changes' using errcode = '22023';
  end if;
  if review_spec.verdict = 'changes_requested' and said is null then
    raise exception 'Say what to change' using errcode = '23514';
  end if;
  update public.spec_reviews
  set verdict = review_spec.verdict, note = said, answered_at = now()
  where spec_id = spec and reviewer_id = (select auth.uid());
  if not exists (
    select from public.spec_reviews r where r.spec_id = spec and r.verdict <> 'approved'
  ) then
    update public.specs set status = 'approved' where id = spec;
    return 'approved';
  end if;
  return target.status;
end;
$$;

revoke execute on function public.request_review(uuid, uuid) from public, anon;
revoke execute on function public.remove_reviewer(uuid, uuid) from public, anon;
revoke execute on function public.review_spec(uuid, public.review_verdict, text) from public, anon;
grant execute on function public.request_review(uuid, uuid) to authenticated;
grant execute on function public.remove_reviewer(uuid, uuid) to authenticated;
grant execute on function public.review_spec(uuid, public.review_verdict, text) to authenticated;

-- Everyone in a workspace sees its specs' reviews; they change only through the functions above.
alter table public.spec_reviews enable row level security;
revoke all on public.spec_reviews from anon, authenticated;
grant select on public.spec_reviews to authenticated;

create policy "Members see their workspaces' reviews" on public.spec_reviews
for select to authenticated using (workspace_id in (select access.workspace_ids()));

-- Each criterion's proof names its spec's owner too, so My work finds the criteria failing on a
-- person's own specs.
create or replace view public.criterion_proofs with (security_invoker = true) as
select
  c.id as criterion_id,
  c.workspace_id,
  c.spec_id,
  s.number as spec_number,
  s.title as spec_title,
  s.status as spec_status,
  c.number as criterion_number,
  c.text,
  c.suspect_since,
  count(t.id)::integer as tests,
  (count(t.id) filter (where t.outcome = 'passed'))::integer as passed,
  (count(t.id) filter (where t.outcome = 'failed'))::integer as failed,
  (count(t.id) filter (where t.outcome = 'skipped'))::integer as skipped,
  case
    when count(t.id) filter (where t.outcome = 'failed') > 0 then 'failing'
    when c.suspect_since is null and count(t.id) > 0
      and count(t.id) = count(t.id) filter (where t.outcome = 'passed') then 'proven'
    else 'unproven'
  end::public.proof as state,
  max(t.received_at) as checked_at,
  s.owner_id as spec_owner_id
from public.criteria c
join public.specs s on s.id = c.spec_id
left join public.latest_claims t
  on t.workspace_id = c.workspace_id and t.spec_number = s.number and t.criterion_number = c.number
group by c.id, s.id;
