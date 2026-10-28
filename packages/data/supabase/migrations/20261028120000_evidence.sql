-- Test results from a workspace's CI, and what they prove (decision record 50). A team adds its
-- GitHub repositories, and a step in each workflow sends the run's JUnit XML report, signed with
-- the run's OpenID Connect token. The site's Worker checks the token and passes the report here,
-- where Postgres reads it and keeps each test that names a criterion. A criterion is proven when
-- every test that names it passed in the latest report of its suite on its repository's branch.

create table public.repositories (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces (id) on delete cascade,
  -- owner/name, as GitHub writes it.
  name text not null check (
    name ~ '^[A-Za-z0-9-]{1,100}/[A-Za-z0-9_.-]{1,100}$' and split_part(name, '/', 2) not in ('.', '..')
  ),
  -- The branch whose runs prove criteria, usually the default branch.
  branch text not null default 'main' check (branch ~ '^[^\s]{1,255}$'),
  -- GitHub's IDs for the repository and its owner, kept from its first report, so a repository
  -- given the same name later isn't taken for this one.
  github_id bigint,
  owner_github_id bigint,
  added_by uuid references public.people (id) on delete set null,
  added_at timestamptz not null default now(),
  unique (workspace_id, id)
);

create unique index repositories_by_name on public.repositories (workspace_id, lower(name));

create type public.test_outcome as enum ('passed', 'failed', 'skipped');
create type public.proof as enum ('proven', 'failing', 'unproven');

-- One report from one run of a workflow. Only runs on the repository's branch are kept, and the
-- last 20 of each suite.
create table public.test_reports (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null,
  repository_id uuid not null,
  -- The report's name in its workflow, such as "unit", so each suite has a latest report.
  suite text not null check (suite ~ '^[A-Za-z0-9_.-]{1,64}$'),
  branch text not null,
  sha text not null check (sha ~ '^[0-9a-f]{40}$'),
  run_id bigint not null,
  run_attempt integer not null check (run_attempt > 0),
  workflow text not null check (char_length(workflow) <= 255),
  received_at timestamptz not null default now(),
  tests integer not null,
  passed integer not null,
  failed integer not null,
  skipped integer not null,
  foreign key (workspace_id, repository_id) references public.repositories (workspace_id, id)
    on delete cascade,
  unique (repository_id, suite, run_id, run_attempt),
  unique (workspace_id, id)
);

create index test_reports_latest on public.test_reports (repository_id, suite, run_id desc, run_attempt desc);
create index test_reports_by_workspace on public.test_reports (workspace_id, received_at desc);

-- Each test in a report that names a criterion, once for each criterion it names. A test can
-- name a criterion that doesn't exist, such as one not written yet.
create table public.test_claims (
  id bigint generated always as identity primary key,
  workspace_id uuid not null,
  report_id uuid not null,
  spec_number integer not null,
  criterion_number integer not null,
  name text not null,
  classname text not null default '',
  file text,
  outcome public.test_outcome not null,
  -- What the failure said, cut to 500 characters.
  message text,
  foreign key (workspace_id, report_id) references public.test_reports (workspace_id, id)
    on delete cascade
);

-- How many reports each repository has sent in each hour, which record_report alone reads and
-- writes.
create table private.report_hours (
  repository_id uuid not null references public.repositories (id) on delete cascade,
  hour timestamptz not null,
  sent integer not null,
  primary key (repository_id, hour)
);

alter table private.report_hours enable row level security;

create index test_claims_by_criterion on public.test_claims (workspace_id, spec_number, criterion_number);
create index test_claims_by_report on public.test_claims (report_id);

-- When a criterion was reworded while tests named it. Its tests may check the old wording, so
-- it isn't proven again until a member confirms they check the new one.
alter table public.criteria add column suspect_since timestamptz;

create function private.mark_suspect()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.text is distinct from old.text and exists (
    select from public.test_claims t
    join public.specs s on s.id = new.spec_id
    where t.workspace_id = new.workspace_id and t.spec_number = s.number and t.criterion_number = new.number
  ) then
    new.suspect_since := coalesce(old.suspect_since, now());
  end if;
  return new;
end;
$$;

revoke execute on function private.mark_suspect() from public;

create trigger mark_suspect before update of text on public.criteria
for each row execute function private.mark_suspect();

create trigger record_event after insert or update or delete on public.repositories
for each row execute function private.record_event('repository', 'id');

-- The latest report of each suite on each repository's branch.
create view public.latest_reports with (security_invoker = true) as
select distinct on (r.repository_id, r.suite) r.*
from public.test_reports r
join public.repositories p on p.id = r.repository_id and p.branch = r.branch
order by r.repository_id, r.suite, r.run_id desc, r.run_attempt desc;

-- The tests in those reports that name a criterion, with the run each comes from.
create view public.latest_claims with (security_invoker = true) as
select
  t.id,
  t.workspace_id,
  t.spec_number,
  t.criterion_number,
  t.name,
  t.classname,
  t.file,
  t.outcome,
  t.message,
  r.id as report_id,
  r.suite,
  r.sha,
  r.run_id,
  r.run_attempt,
  r.workflow,
  r.received_at,
  p.name as repository
from public.test_claims t
join public.latest_reports r on r.id = t.report_id
join public.repositories p on p.id = r.repository_id;

-- Each criterion's proof: failing when any test that names it failed, proven when every one of
-- them passed and it hasn't been reworded since, and unproven otherwise.
create view public.criterion_proofs with (security_invoker = true) as
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
  max(t.received_at) as checked_at
from public.criteria c
join public.specs s on s.id = c.spec_id
left join public.latest_claims t
  on t.workspace_id = c.workspace_id and t.spec_number = s.number and t.criterion_number = c.number
group by c.id, s.id;

-- How many of each spec's criteria are proven and failing.
create view public.spec_proofs with (security_invoker = true) as
select
  spec_id,
  workspace_id,
  count(*)::integer as criteria,
  (count(*) filter (where state = 'proven'))::integer as proven,
  (count(*) filter (where state = 'failing'))::integer as failing
from public.criterion_proofs
group by spec_id, workspace_id;

-- Adds one of the team's GitHub repositories, whose reports the workspace then takes. Admins and
-- owners add them; a workspace has at most 20.
create function public.add_repository(workspace uuid, name text, branch text default 'main')
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  made uuid;
begin
  if not access.holds(workspace, 'admin') then
    raise exception 'Only admins and owners can add repositories' using errcode = '42501';
  end if;
  if (select count(*) from public.repositories where workspace_id = workspace) >= 20 then
    raise exception 'A workspace can have at most 20 repositories' using errcode = '54000';
  end if;
  if exists (
    select from public.repositories
    where workspace_id = workspace and lower(repositories.name) = lower(btrim(add_repository.name))
  ) then
    raise exception 'This workspace already has that repository' using errcode = '23505';
  end if;
  insert into public.repositories (workspace_id, name, branch, added_by)
  values (workspace, btrim(add_repository.name), btrim(add_repository.branch), (select auth.uid()))
  returning id into made;
  return made;
end;
$$;

-- Confirms that a reworded criterion's tests check its new wording, so they can prove it again.
create function public.confirm_criterion(criterion uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  workspace uuid := (select workspace_id from public.criteria where id = criterion);
begin
  if workspace is null or not access.holds(workspace, 'member') then
    raise exception 'Only members can confirm a criterion''s tests' using errcode = '42501';
  end if;
  update public.criteria set suspect_since = null where id = criterion;
end;
$$;

-- A test case as a report gives it.
create type private.test_case as (
  name text,
  classname text,
  file text,
  outcome public.test_outcome,
  message text
);

-- Takes a report sent from a workflow run. Only the site's Worker calls it, once it has checked
-- the run's token, and passes the token's claims as run: repository, repository_id,
-- repository_owner_id, ref, sha, run_id, run_attempt and workflow. The report is one or more
-- JUnit XML documents. Says what it kept, for the run's log.
create function public.record_report(workspace text, suite text, run jsonb, reports text[])
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
#variable_conflict use_column
declare
  place uuid := (select id from public.workspaces where slug = workspace);
  repository public.repositories;
  cases private.test_case[];
  report uuid;
  kept jsonb;
  sent integer;
begin
  select * into repository from public.repositories
  where workspace_id = place and lower(name) = lower(run ->> 'repository');
  if repository.id is null then
    raise exception 'sulba.dev/app/% takes no reports from %. Check the workspace''s address, and that an admin has added the repository in Settings',
      workspace, run ->> 'repository' using errcode = 'P0002';
  end if;
  if repository.github_id is null then
    update public.repositories
    set github_id = (run ->> 'repository_id')::bigint, owner_github_id = (run ->> 'repository_owner_id')::bigint
    where id = repository.id;
  elsif repository.github_id <> (run ->> 'repository_id')::bigint then
    raise exception '% is no longer the repository this workspace added. An admin can remove it in Settings and add it again',
      repository.name using errcode = '42501';
  end if;
  if run ->> 'ref' is distinct from 'refs/heads/' || repository.branch then
    return jsonb_build_object('kept', false, 'branch', repository.branch);
  end if;
  delete from private.report_hours
  where repository_id = repository.id and hour < date_trunc('hour', now()) - interval '1 day';
  insert into private.report_hours as h (repository_id, hour, sent)
  values (repository.id, date_trunc('hour', now()), 1)
  on conflict (repository_id, hour) do update set sent = h.sent + 1
  returning h.sent into sent;
  if sent > 120 then
    raise exception 'A repository can send at most 120 reports an hour' using errcode = '54000';
  end if;

  begin
    select coalesce(array_agg(row(
      left(coalesce(x.name, ''), 1000),
      left(coalesce(x.classname, ''), 1000),
      left(x.file, 1000),
      case when x.failed then 'failed' when x.skipped then 'skipped' else 'passed' end::public.test_outcome,
      case when x.failed then left(btrim(coalesce(nullif(x.reason, ''), x.detail)), 500) end
    )::private.test_case), '{}')
    into cases
    from unnest(reports) as each (document),
    lateral xmltable(
      '//testcase' passing xmlparse(document each.document)
      columns
        name text path '@name',
        classname text path '@classname',
        file text path '@file',
        failed boolean path 'boolean(failure|error)',
        skipped boolean path 'boolean(skipped)',
        reason text path 'string((failure|error)[1]/@message)',
        detail text path 'substring(normalize-space((failure|error)[1]), 1, 500)'
    ) as x;
  exception when data_exception then
    raise exception 'The report isn''t JUnit XML: %', sqlerrm using errcode = '22023';
  end;
  if cardinality(cases) > 100000 then
    raise exception 'A report can hold at most 100,000 tests' using errcode = '54000';
  end if;

  insert into public.test_reports (
    workspace_id, repository_id, suite, branch, sha, run_id, run_attempt, workflow,
    tests, passed, failed, skipped
  )
  select
    place, repository.id, record_report.suite, repository.branch, run ->> 'sha',
    (run ->> 'run_id')::bigint, (run ->> 'run_attempt')::integer, left(run ->> 'workflow', 255),
    count(*), count(*) filter (where c.outcome = 'passed'), count(*) filter (where c.outcome = 'failed'),
    count(*) filter (where c.outcome = 'skipped')
  from unnest(cases) as c
  on conflict (repository_id, suite, run_id, run_attempt) do update
    set received_at = now(), sha = excluded.sha, tests = excluded.tests, passed = excluded.passed,
      failed = excluded.failed, skipped = excluded.skipped
  returning id into report;

  -- A report sent again replaces what it said before.
  delete from public.test_claims where report_id = report;
  insert into public.test_claims (
    workspace_id, report_id, spec_number, criterion_number, name, classname, file, outcome, message
  )
  select distinct place, report, m[1]::integer, m[2]::integer, c.name, c.classname, c.file, c.outcome, c.message
  from unnest(cases) as c,
  lateral regexp_matches(c.name, 'spec[-_/ ]([1-9][0-9]{0,8})[-_/ ]ac[-_/ ]([1-9][0-9]{0,8})(?![0-9])', 'gi') as m;

  delete from public.test_reports
  where repository_id = repository.id and test_reports.suite = record_report.suite and id not in (
    select id from public.test_reports
    where repository_id = repository.id and test_reports.suite = record_report.suite
    order by run_id desc, run_attempt desc
    limit 20
  );

  select coalesce(jsonb_agg(jsonb_build_object(
    'spec', claim.spec_number,
    'criterion', claim.criterion_number,
    'outcome', claim.outcome,
    'known', exists (
      select from public.criteria k join public.specs s on s.id = k.spec_id
      where s.workspace_id = place and s.number = claim.spec_number and k.number = claim.criterion_number
    )
  ) order by claim.spec_number, claim.criterion_number), '[]')
  into kept
  from (
    select spec_number, criterion_number,
      case
        when bool_or(outcome = 'failed') then 'failed'
        when bool_and(outcome = 'passed') then 'passed'
        else 'skipped'
      end as outcome
    from public.test_claims where report_id = report
    group by spec_number, criterion_number
  ) as claim;

  return jsonb_build_object(
    'kept', true,
    'branch', repository.branch,
    'tests', cardinality(cases),
    'passed', (select count(*) from unnest(cases) c where c.outcome = 'passed'),
    'failed', (select count(*) from unnest(cases) c where c.outcome = 'failed'),
    'skipped', (select count(*) from unnest(cases) c where c.outcome = 'skipped'),
    'criteria', kept
  );
end;
$$;

revoke execute on function public.add_repository(uuid, text, text) from public, anon;
revoke execute on function public.confirm_criterion(uuid) from public, anon;
revoke execute on function public.record_report(text, text, jsonb, text[]) from public, anon, authenticated;
grant execute on function public.add_repository(uuid, text, text) to authenticated;
grant execute on function public.confirm_criterion(uuid) to authenticated;
grant execute on function public.record_report(text, text, jsonb, text[]) to service_role;

-- Everyone in a workspace reads its repositories, reports and proofs; admins add and remove
-- repositories and choose their branch. Only the Worker, through record_report, writes reports.
alter table public.repositories enable row level security;
alter table public.test_reports enable row level security;
alter table public.test_claims enable row level security;

revoke all on public.repositories, public.test_reports, public.test_claims,
  public.latest_reports, public.latest_claims, public.criterion_proofs, public.spec_proofs
from anon, authenticated;
grant select on public.repositories, public.test_reports, public.test_claims,
  public.latest_reports, public.latest_claims, public.criterion_proofs, public.spec_proofs
to authenticated;
grant update (branch) on public.repositories to authenticated;
grant delete on public.repositories to authenticated;

create policy "Members see their workspaces' repositories" on public.repositories
for select to authenticated using (workspace_id in (select access.workspace_ids()));

create policy "Admins choose a repository's branch" on public.repositories
for update to authenticated
using (workspace_id in (select access.workspace_ids('admin')))
with check (workspace_id in (select access.workspace_ids('admin')));

create policy "Admins remove repositories" on public.repositories
for delete to authenticated using (workspace_id in (select access.workspace_ids('admin')));

create policy "Members see their workspaces' reports" on public.test_reports
for select to authenticated using (workspace_id in (select access.workspace_ids()));

create policy "Members see their workspaces' tests" on public.test_claims
for select to authenticated using (workspace_id in (select access.workspace_ids()));
