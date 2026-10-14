-- A learner's progress, kept as a log of what they did in each stage. The browser adds attempts,
-- and Postgres keeps each stage's progress and each day studied up to date from them (decision
-- record 18). Every row belongs to one signed-in learner, and only they can read it.

-- Functions only the database calls, outside the schemas the Data API serves.
create schema private;

create table public.attempts (
  -- Made by the browser, so a batch sent twice adds nothing the second time.
  id uuid primary key,
  learner_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  stage_id text not null check (stage_id ~ '^stg_[0-9a-z]{6}$'),
  -- A hash of the stage's files when it happened, so progress can tell when a stage has changed.
  stage_version text not null check (stage_version ~ '^[0-9a-f]{16}$'),
  kind text not null check (kind in ('run', 'hint', 'solution', 'pass')),
  -- A run: how many of its tests passed and, in a Catch or Ship stage, how many of its checks.
  tests_passed smallint,
  tests_total smallint,
  checks_passed smallint,
  checks_total smallint,
  -- A hint: which one the learner opened.
  hint smallint check (hint between 1 and 50),
  -- A Catch stage's pass: the checks of the problems the learner caught, and how many it has.
  caught text[],
  problems smallint check (problems between 1 and 50),
  -- Time on the stage since the learner's last attempt there, as the workspace measured it.
  seconds integer not null default 0 check (seconds between 0 and 3600),
  -- When it happened by the learner's clock, and the day it was in their time zone.
  happened_at timestamptz not null,
  day date not null,
  -- When it arrived, by the database's clock.
  created_at timestamptz not null default now(),
  constraint run_has_tests check ((kind = 'run') = (tests_passed is not null and tests_total is not null)),
  constraint tests_in_range check (tests_passed between 0 and tests_total),
  constraint checks_on_runs check (kind = 'run' or checks_total is null),
  constraint checks_in_range check (
    (checks_passed is null) = (checks_total is null) and checks_passed between 0 and checks_total
  ),
  constraint hint_has_number check ((kind = 'hint') = (hint is not null)),
  constraint review_on_pass check (kind = 'pass' or problems is null),
  constraint review_whole check ((caught is null) = (problems is null)),
  constraint caught_in_range check (cardinality(caught) <= problems),
  constraint caught_are_checks check (
    array_to_string(caught, ',') ~ '^(tst_[0-9a-z]{6}(,tst_[0-9a-z]{6})*)?$'
  ),
  constraint day_of_happened check (
    day between (happened_at at time zone 'utc')::date - 1 and (happened_at at time zone 'utc')::date + 1
  ),
  constraint happened_before_arrival check (happened_at < created_at + interval '1 day')
);

-- Serves the row-level security policies and the daily limit below.
create index attempts_by_learner on public.attempts (learner_id, created_at);

create table public.progress (
  learner_id uuid not null references auth.users (id) on delete cascade,
  stage_id text not null,
  runs integer not null default 0,
  -- The most hints opened.
  hints smallint not null default 0,
  solution_viewed boolean not null default false,
  seconds integer not null default 0,
  -- The first pass, whichever device sends it first: when it happened, the stage's version then,
  -- and in a Catch stage the review it finished.
  passed_at timestamptz,
  passed_version text,
  caught text[],
  problems smallint,
  primary key (learner_id, stage_id)
);

create table public.study_days (
  learner_id uuid not null references auth.users (id) on delete cascade,
  day date not null,
  seconds integer not null default 0,
  primary key (learner_id, day)
);

-- One account can't fill the free plan's 500 MB: past 2,000 attempts in a day, more are refused.
create function private.limit_attempts()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if (
    select count(*) from public.attempts
    where learner_id = new.learner_id and created_at > now() - interval '1 day'
  ) >= 2000 then
    raise exception 'More than 2,000 attempts in a day';
  end if;
  return new;
end;
$$;

create trigger limit_attempts
before insert on public.attempts
for each row execute function private.limit_attempts();

-- Folds each attempt into its stage's progress and its day. Attempts can arrive in any order and
-- from several devices, so every change is one that order doesn't affect: counts add up, the
-- most hints wins, and the earliest pass wins.
create function private.record_attempt()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.progress as p (
    learner_id, stage_id, runs, hints, solution_viewed, seconds,
    passed_at, passed_version, caught, problems
  )
  values (
    new.learner_id, new.stage_id, (new.kind = 'run')::integer, coalesce(new.hint, 0),
    new.kind = 'solution', new.seconds,
    case when new.kind = 'pass' then new.happened_at end,
    case when new.kind = 'pass' then new.stage_version end,
    new.caught, new.problems
  )
  on conflict (learner_id, stage_id) do update set
    runs = p.runs + excluded.runs,
    hints = greatest(p.hints, excluded.hints),
    solution_viewed = p.solution_viewed or excluded.solution_viewed,
    seconds = p.seconds + excluded.seconds,
    passed_at = least(p.passed_at, excluded.passed_at),
    passed_version = case
      when excluded.passed_at < coalesce(p.passed_at, 'infinity') then excluded.passed_version
      else p.passed_version
    end,
    caught = case
      when excluded.passed_at < coalesce(p.passed_at, 'infinity') then excluded.caught
      else p.caught
    end,
    problems = case
      when excluded.passed_at < coalesce(p.passed_at, 'infinity') then excluded.problems
      else p.problems
    end;

  insert into public.study_days as d (learner_id, day, seconds)
  values (new.learner_id, new.day, new.seconds)
  on conflict (learner_id, day) do update set seconds = d.seconds + excluded.seconds;

  return null;
end;
$$;

create trigger record_attempt
after insert on public.attempts
for each row execute function private.record_attempt();

revoke execute on all functions in schema private from public;

-- Only signed-in learners reach these tables, and only their own rows. An attempt can't be changed
-- or removed once sent, and progress and study days change only through attempts. The arrival
-- time is the database's, so the daily limit can't be dodged.
alter table public.attempts enable row level security;
alter table public.progress enable row level security;
alter table public.study_days enable row level security;

revoke all on public.attempts, public.progress, public.study_days from anon, authenticated;
grant select on public.attempts, public.progress, public.study_days to authenticated;
grant insert (
  id, learner_id, stage_id, stage_version, kind, tests_passed, tests_total, checks_passed,
  checks_total, hint, caught, problems, seconds, happened_at, day
) on public.attempts to authenticated;

create policy "Learners add their own attempts" on public.attempts
for insert to authenticated with check (learner_id = (select auth.uid()));

create policy "Learners read their own attempts" on public.attempts
for select to authenticated using (learner_id = (select auth.uid()));

create policy "Learners read their own progress" on public.progress
for select to authenticated using (learner_id = (select auth.uid()));

create policy "Learners read their own study days" on public.study_days
for select to authenticated using (learner_id = (select auth.uid()));
