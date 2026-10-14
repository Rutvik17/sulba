-- A learner reaches only their own rows, and their progress and study days follow their attempts
-- in whatever order those arrive.
begin;
select plan(41);

insert into auth.users (id, email) values
  ('a0000000-0000-4000-8000-000000000001', 'a@example.com'),
  ('b0000000-0000-4000-8000-000000000002', 'b@example.com'),
  ('c0000000-0000-4000-8000-000000000003', 'c@example.com');

select is(
  (
    select count(*)::integer from pg_class
    where relnamespace = 'public'::regnamespace and relkind = 'r' and not relrowsecurity
  ),
  0,
  'Every table in public has row-level security'
);
select schema_privs_are('private', 'anon', array[]::text[], 'Visitors can''t reach the private schema');
select schema_privs_are('private', 'authenticated', array[]::text[], 'nor can learners');

-- Without signing in, nothing.
set local role anon;

select throws_ok('select * from public.attempts', '42501', null, 'Visitors can''t read attempts');
select throws_ok('select * from public.progress', '42501', null, 'Visitors can''t read progress');
select throws_ok('select * from public.study_days', '42501', null, 'Visitors can''t read study days');
select throws_ok(
  $$insert into public.attempts (id, learner_id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
    values ('10000000-0000-4000-8000-000000000000', 'a0000000-0000-4000-8000-000000000001', 'stg_aaaaaa',
      '0123456789abcdef', 'run', 0, 6, '2026-10-14 09:00+00', '2026-10-14')$$,
  '42501',
  null,
  'Visitors can''t add attempts'
);

-- Learner A runs a stage's tests, opens hints and the solution, and passes.
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);

select lives_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, seconds, happened_at, day)
    values ('10000000-0000-4000-8000-000000000001', 'stg_aaaaaa', '0123456789abcdef', 'run', 2, 6, 300,
      '2026-10-14 10:00+00', '2026-10-14')$$,
  'A learner adds a run'
);
select is(
  (select learner_id from public.attempts where id = '10000000-0000-4000-8000-000000000001'),
  'a0000000-0000-4000-8000-000000000001'::uuid,
  'An attempt belongs to the signed-in learner'
);
select is(
  (select runs from public.progress where stage_id = 'stg_aaaaaa'),
  1,
  'A run counts in the stage''s progress'
);

select lives_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, seconds, happened_at, day)
    values ('10000000-0000-4000-8000-000000000001', 'stg_aaaaaa', '0123456789abcdef', 'run', 2, 6, 300,
      '2026-10-14 10:00+00', '2026-10-14')
    on conflict (id) do nothing$$,
  'A batch sent again is accepted'
);
select is(
  (select runs from public.progress where stage_id = 'stg_aaaaaa'),
  1,
  'and adds nothing'
);

insert into public.attempts (id, stage_id, stage_version, kind, hint, seconds, happened_at, day) values
  ('10000000-0000-4000-8000-000000000002', 'stg_aaaaaa', '0123456789abcdef', 'hint', 2, 60, '2026-10-14 10:05+00', '2026-10-14'),
  ('10000000-0000-4000-8000-000000000003', 'stg_aaaaaa', '0123456789abcdef', 'hint', 1, 30, '2026-10-14 10:02+00', '2026-10-14');
select is(
  (select hints from public.progress where stage_id = 'stg_aaaaaa'),
  2::smallint,
  'Progress keeps the most hints opened, whatever order they arrive in'
);

insert into public.attempts (id, stage_id, stage_version, kind, seconds, happened_at, day)
values ('10000000-0000-4000-8000-000000000004', 'stg_aaaaaa', '0123456789abcdef', 'solution', 10, '2026-10-14 10:06+00', '2026-10-14');
select ok(
  (select solution_viewed from public.progress where stage_id = 'stg_aaaaaa'),
  'Progress records that the solution was viewed'
);

-- A Catch stage passed on two devices: the later review arrives first.
insert into public.attempts (id, stage_id, stage_version, kind, caught, problems, seconds, happened_at, day) values
  ('10000000-0000-4000-8000-000000000005', 'stg_bbbbbb', '1111111111111111', 'pass', '{tst_aaaaaa}', 3, 600, '2026-10-13 12:00+00', '2026-10-13'),
  ('10000000-0000-4000-8000-000000000006', 'stg_bbbbbb', '2222222222222222', 'pass', '{tst_aaaaaa,tst_bbbbbb}', 3, 900, '2026-10-13 11:00+00', '2026-10-13'),
  ('10000000-0000-4000-8000-000000000007', 'stg_bbbbbb', '3333333333333333', 'pass', '{}', 3, 0, '2026-10-13 13:00+00', '2026-10-13');
select results_eq(
  $$select passed_at, passed_version, caught, problems from public.progress where stage_id = 'stg_bbbbbb'$$,
  $$values ('2026-10-13 11:00+00'::timestamptz, '2222222222222222', '{tst_aaaaaa,tst_bbbbbb}'::text[], 3::smallint)$$,
  'The earliest pass counts, with its review, whichever arrives first'
);

select results_eq(
  'select day, seconds from public.study_days order by day',
  $$values ('2026-10-13'::date, 1500), ('2026-10-14'::date, 400)$$,
  'Study days add up the time from each day''s attempts'
);
select is(
  (select seconds from public.progress where stage_id = 'stg_aaaaaa'),
  400,
  'Progress adds up the time on its stage'
);

-- What a learner can't do.
select throws_ok(
  $$insert into public.attempts (id, learner_id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
    values ('10000000-0000-4000-8000-000000000008', 'b0000000-0000-4000-8000-000000000002', 'stg_aaaaaa',
      '0123456789abcdef', 'run', 6, 6, '2026-10-14 11:00+00', '2026-10-14')$$,
  '42501',
  null,
  'A learner can''t add an attempt for someone else'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day, created_at)
    values ('10000000-0000-4000-8000-000000000009', 'stg_aaaaaa', '0123456789abcdef', 'run', 6, 6,
      '2026-10-14 11:00+00', '2026-10-14', '2026-01-01')$$,
  '42501',
  null,
  'A learner can''t set when an attempt arrived'
);
select throws_ok(
  'update public.attempts set tests_passed = 6',
  '42501',
  null,
  'A learner can''t change an attempt'
);
select throws_ok('delete from public.attempts', '42501', null, 'A learner can''t remove an attempt');
select throws_ok(
  $$insert into public.progress (learner_id, stage_id, passed_at)
    values ('a0000000-0000-4000-8000-000000000001', 'stg_cccccc', now())$$,
  '42501',
  null,
  'A learner can''t write progress directly'
);
select throws_ok(
  'update public.progress set runs = 0',
  '42501',
  null,
  'A learner can''t change progress'
);
select throws_ok(
  $$insert into public.study_days (learner_id, day) values ('a0000000-0000-4000-8000-000000000001', '2026-10-01')$$,
  '42501',
  null,
  'A learner can''t write study days directly'
);

-- Attempts that make no sense are refused.
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
    values ('10000000-0000-4000-8000-000000000010', 'logistic', '0123456789abcdef', 'run', 6, 6, '2026-10-14 11:00+00', '2026-10-14')$$,
  '23514',
  null,
  'A stage is named by its permanent id'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, happened_at, day)
    values ('10000000-0000-4000-8000-000000000011', 'stg_aaaaaa', '0123456789abcdef', 'run', '2026-10-14 11:00+00', '2026-10-14')$$,
  '23514',
  null,
  'A run says how many tests passed'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
    values ('10000000-0000-4000-8000-000000000012', 'stg_aaaaaa', '0123456789abcdef', 'run', 7, 6, '2026-10-14 11:00+00', '2026-10-14')$$,
  '23514',
  null,
  'A run can''t pass more tests than it has'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, happened_at, day)
    values ('10000000-0000-4000-8000-000000000013', 'stg_aaaaaa', '0123456789abcdef', 'hint', '2026-10-14 11:00+00', '2026-10-14')$$,
  '23514',
  null,
  'A hint says which one was opened'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, caught, problems, happened_at, day)
    values ('10000000-0000-4000-8000-000000000014', 'stg_aaaaaa', '0123456789abcdef', 'run', 6, 6, '{}', 3, '2026-10-14 11:00+00', '2026-10-14')$$,
  '23514',
  null,
  'Only a pass carries a review'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, caught, problems, happened_at, day)
    values ('10000000-0000-4000-8000-000000000015', 'stg_bbbbbb', '0123456789abcdef', 'pass', '{every-problem}', 3, '2026-10-14 11:00+00', '2026-10-14')$$,
  '23514',
  null,
  'A review names the checks of the problems caught'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, caught, problems, happened_at, day)
    values ('10000000-0000-4000-8000-000000000016', 'stg_bbbbbb', '0123456789abcdef', 'pass', '{tst_aaaaaa,tst_bbbbbb}', 1, '2026-10-14 11:00+00', '2026-10-14')$$,
  '23514',
  null,
  'A review can''t catch more problems than it has'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
    values ('10000000-0000-4000-8000-000000000017', 'stg_aaaaaa', '0123456789abcdef', 'run', 6, 6, '2026-10-14 11:00+00', '2026-10-17')$$,
  '23514',
  null,
  'A day is the one the attempt happened in'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
    values ('10000000-0000-4000-8000-000000000018', 'stg_aaaaaa', '0123456789abcdef', 'run', 6, 6, now() + interval '2 days', (now() + interval '2 days')::date)$$,
  '23514',
  null,
  'An attempt can''t happen in the future'
);

-- Learner B sees none of it.
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);

select is_empty('select * from public.attempts', 'Another learner can''t read the attempts');
select is_empty('select * from public.progress', 'or the progress');
select is_empty('select * from public.study_days', 'or the study days');

insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
values ('20000000-0000-4000-8000-000000000001', 'stg_aaaaaa', '0123456789abcdef', 'run', 6, 6, '2026-10-14 12:00+00', '2026-10-14');
select results_eq(
  'select learner_id, runs from public.progress',
  $$values ('b0000000-0000-4000-8000-000000000002'::uuid, 1)$$,
  'Each learner reads only their own progress'
);

-- Learner C reaches the daily limit.
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);

select lives_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
    select gen_random_uuid(), 'stg_aaaaaa', '0123456789abcdef', 'run', 0, 6, now(), (now() at time zone 'utc')::date
    from generate_series(1, 2000)$$,
  'A learner can add 2,000 attempts in a day'
);
select throws_ok(
  $$insert into public.attempts (id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
    values (gen_random_uuid(), 'stg_aaaaaa', '0123456789abcdef', 'run', 0, 6, now(), (now() at time zone 'utc')::date)$$,
  'P0001',
  'More than 2,000 attempts in a day',
  'but no more'
);

-- Closing an account removes everything it recorded.
reset role;
delete from auth.users where id = 'a0000000-0000-4000-8000-000000000001';

select is(
  (select count(*)::integer from public.attempts where learner_id = 'a0000000-0000-4000-8000-000000000001'),
  0,
  'Closing an account removes its attempts'
);
select is(
  (
    select count(*)::integer from public.progress
    where learner_id = 'a0000000-0000-4000-8000-000000000001'
  ) + (
    select count(*)::integer from public.study_days
    where learner_id = 'a0000000-0000-4000-8000-000000000001'
  ),
  0,
  'and its progress and study days'
);

select * from finish();
rollback;
