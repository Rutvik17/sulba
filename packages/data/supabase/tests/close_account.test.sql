-- Closing an account removes that learner and what they recorded, and no one else's.
begin;
select plan(5);

insert into auth.users (id, email) values
  ('a0000000-0000-4000-8000-000000000001', 'a@example.com'),
  ('b0000000-0000-4000-8000-000000000002', 'b@example.com');

insert into public.attempts (id, learner_id, stage_id, stage_version, kind, tests_passed, tests_total, happened_at, day)
values
  ('10000000-0000-4000-8000-000000000001', 'a0000000-0000-4000-8000-000000000001', 'stg_aaaaaa',
    '0123456789abcdef', 'run', 6, 6, '2026-10-14 10:00+00', '2026-10-14'),
  ('20000000-0000-4000-8000-000000000001', 'b0000000-0000-4000-8000-000000000002', 'stg_aaaaaa',
    '0123456789abcdef', 'run', 6, 6, '2026-10-14 10:00+00', '2026-10-14');

set local role anon;
select throws_ok('select public.close_account()', '42501', null, 'Visitors can''t close an account');

set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);
select lives_ok('select public.close_account()', 'A learner closes their account');

reset role;
select is(
  (select count(*)::integer from auth.users where id = 'a0000000-0000-4000-8000-000000000001'),
  0,
  'The account is gone'
);
select is(
  (select count(*)::integer from public.progress where learner_id = 'a0000000-0000-4000-8000-000000000001'),
  0,
  'with its progress'
);
select results_eq(
  'select learner_id from public.progress',
  $$values ('b0000000-0000-4000-8000-000000000002'::uuid)$$,
  'Another learner''s account and progress stay'
);

select * from finish();
rollback;
