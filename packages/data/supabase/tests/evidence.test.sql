-- A workspace takes reports only from the repositories its admins add, only the Worker sends
-- them, and each criterion's proof follows the latest report of each suite on the repository's
-- branch.
begin;
select plan(41);

insert into auth.users (id, email, raw_user_meta_data) values
  ('a0000000-0000-4000-8000-000000000001', 'ada@example.com', '{"full_name": "Ada Lovelace"}'),
  ('b0000000-0000-4000-8000-000000000002', 'ben@example.com', '{"name": "Ben"}'),
  ('c0000000-0000-4000-8000-000000000003', 'cy@example.com', '{}'),
  ('d0000000-0000-4000-8000-000000000004', 'dee@example.com', '{}');

-- A run's claims as the Worker passes them, and a JUnit XML report of the given test cases.
create function pg_temp.run(id integer, ref text default 'refs/heads/main', repository_id text default '101')
returns jsonb language sql as $$
  select jsonb_build_object(
    'repository', 'acme-co/payments', 'repository_id', repository_id, 'repository_owner_id', '55',
    'ref', ref, 'sha', repeat('a', 40), 'run_id', id::text, 'run_attempt', '1', 'workflow', 'CI'
  )
$$;
create function pg_temp.report(cases text) returns text[] language sql as $$
  select array['<?xml version="1.0" encoding="UTF-8"?><testsuites><testsuite name="tests">' || cases || '</testsuite></testsuites>']
$$;
create function pg_temp.proofs(spec integer) returns table (criterion integer, state text) language sql as $$
  select criterion_number, state::text from public.criterion_proofs where spec_number = spec order by criterion_number
$$;

select ok(
  not has_function_privilege('authenticated', 'public.record_report(text, text, jsonb, text[])', 'execute'),
  'Signed-in people can''t send reports'
);
select ok(
  not has_function_privilege('anon', 'public.add_repository(uuid, text, text)', 'execute'),
  'Visitors can''t add repositories'
);

-- Ada's workspace, with Ben as a member and Cy as a viewer, and Dee's own.
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);
select set_config('test.acme', (select id::text from public.create_workspace('Acme', 'acme')), true);
select set_config('test.member', public.create_invitation(current_setting('test.acme')::uuid, 'member'), true);
select set_config('test.viewer', public.create_invitation(current_setting('test.acme')::uuid, 'viewer'), true);
select public.create_spec(
  current_setting('test.acme')::uuid, 'Retry failed payments',
  array['Retries once after 30 seconds', 'Keeps the idempotency key', 'Logs the retry', 'Shows it on the invoice']
);
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);
select public.accept_invitation(current_setting('test.member'));
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);
select public.accept_invitation(current_setting('test.viewer'));
select set_config('request.jwt.claims', '{"sub": "d0000000-0000-4000-8000-000000000004", "role": "authenticated"}', true);
select public.create_workspace('Delta', 'delta');

-- Without signing in, nothing.
reset role;
set local role anon;
select throws_ok('select id from public.repositories', '42501', null, 'Visitors can''t read repositories');
select throws_ok('select state from public.criterion_proofs', '42501', null, 'or proofs');

-- Admins add the repositories a workspace takes reports from.
reset role;
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);
select throws_ok(
  $$select public.add_repository(current_setting('test.acme')::uuid, 'acme-co/payments')$$,
  '42501', 'Only admins and owners can add repositories', 'A member can''t add a repository'
);
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);
select lives_ok(
  $$select public.add_repository(current_setting('test.acme')::uuid, ' acme-co/payments ')$$,
  'An owner adds one'
);
select results_eq(
  'select name, branch, github_id from public.repositories',
  $$values ('acme-co/payments', 'main', null::bigint)$$,
  'on its main branch, its GitHub ID not known yet'
);
select throws_ok(
  $$select public.add_repository(current_setting('test.acme')::uuid, 'ACME-CO/Payments')$$,
  '23505', 'This workspace already has that repository', 'A repository is added once'
);
select throws_ok(
  $$select public.add_repository(current_setting('test.acme')::uuid, 'payments')$$,
  '23514', null, 'A repository''s name is owner/name'
);
select is(
  (select action from public.events where subject_type = 'repository' order by id desc limit 1),
  'repository.created',
  'The history records it'
);

-- The Worker sends a report.
reset role;
set local role service_role;
select set_config('request.jwt.claims', '{"role": "service_role"}', true);
select set_config('test.kept', public.record_report('acme', 'unit', pg_temp.run(1000), pg_temp.report($$
  <testcase classname="tests.test_pay" name="test_SPEC_1_AC_1_retries_once" file="tests/test_pay.py" time="0.2"/>
  <testcase classname="tests.test_pay" name="SPEC-1/AC-2 keeps the key"><failure message="expected key k1">Traceback</failure></testcase>
  <testcase classname="tests.test_pay" name="spec 1 ac 3 is logged"><skipped/></testcase>
  <testcase classname="tests.test_pay" name="checkout works"/>
  <testcase classname="tests.test_pay" name="SPEC-9/AC-1 and SPEC-1/AC-1 together"/>
$$))::text, true);
select is(
  current_setting('test.kept')::jsonb - 'criteria',
  '{"kept": true, "branch": "main", "tests": 5, "passed": 3, "failed": 1, "skipped": 1}'::jsonb,
  'A report on main is kept, with its counts'
);
select is(
  current_setting('test.kept')::jsonb -> 'criteria',
  '[{"spec": 1, "criterion": 1, "outcome": "passed", "known": true},
    {"spec": 1, "criterion": 2, "outcome": "failed", "known": true},
    {"spec": 1, "criterion": 3, "outcome": "skipped", "known": true},
    {"spec": 9, "criterion": 1, "outcome": "passed", "known": false}]'::jsonb,
  'and says which criteria its tests name, including one that doesn''t exist'
);
select is((select github_id from public.repositories), 101::bigint, 'The repository''s GitHub ID is kept');
select throws_ok(
  $$select public.record_report('acme', 'unit', pg_temp.run(1001, repository_id => '999'), pg_temp.report('<testcase name="a"/>'))$$,
  '42501', null, 'and a different repository with its name is refused'
);
select throws_ok(
  $$select public.record_report('delta', 'unit', pg_temp.run(1001), pg_temp.report('<testcase name="a"/>'))$$,
  'P0002', null, 'A workspace that hasn''t added the repository takes nothing from it'
);
select is(
  public.record_report('acme', 'unit', pg_temp.run(1001, 'refs/pull/7/merge'), pg_temp.report('<testcase name="test_SPEC_1_AC_2"/>')),
  '{"kept": false, "branch": "main"}'::jsonb,
  'A report from another branch isn''t kept'
);
select throws_ok(
  $$select public.record_report('acme', 'unit', pg_temp.run(1001), array['<testsuites><testcase'])$$,
  '22023', null, 'and one that isn''t XML is refused'
);
select is((select count(*) from public.test_reports), 1::bigint, 'so only the one report is kept');

-- What it proves, as a viewer sees it.
reset role;
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);
select results_eq(
  'select * from pg_temp.proofs(1)',
  $$values (1, 'proven'), (2, 'failing'), (3, 'unproven'), (4, 'unproven')$$,
  'A criterion whose tests passed is proven, one whose test failed is failing, and skipped or untested ones are unproven'
);
select results_eq(
  'select criteria, proven, failing from public.spec_proofs',
  $$values (4, 1, 1)$$,
  'The spec''s proof counts them'
);
select results_eq(
  $$select name, outcome::text, message, repository, suite from public.latest_claims where spec_number = 1 and criterion_number = 2$$,
  $$values ('SPEC-1/AC-2 keeps the key', 'failed', 'expected key k1', 'acme-co/payments', 'unit')$$,
  'A failing test keeps what its failure said'
);
select is(
  (select count(*) from public.test_claims where name = 'SPEC-9/AC-1 and SPEC-1/AC-1 together'),
  2::bigint,
  'A test that names two criteria claims both'
);
select set_config('request.jwt.claims', '{"sub": "d0000000-0000-4000-8000-000000000004", "role": "authenticated"}', true);
select is((select count(*) from public.test_reports), 0::bigint, 'Other workspaces see none of it');

-- The latest run of each suite decides.
reset role;
set local role service_role;
select public.record_report('acme', 'unit', pg_temp.run(1002), pg_temp.report(
  '<testcase name="test_SPEC_1_AC_1"/><testcase name="test_SPEC_1_AC_2"/>'
));
select public.record_report('acme', 'unit', pg_temp.run(999), pg_temp.report(
  '<testcase name="test_SPEC_1_AC_1"/><testcase name="test_SPEC_1_AC_2"><error message="boom"/></testcase>'
));
select public.record_report('acme', 'e2e', pg_temp.run(1002), pg_temp.report(
  '<testcase name="SPEC-1/AC-1 in the browser"><failure/></testcase>'
));
reset role;
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);
select results_eq(
  'select * from pg_temp.proofs(1) where criterion <= 2',
  $$values (1, 'failing'), (2, 'proven')$$,
  'A newer run proves AC-2, an older one sent later doesn''t undo it, and AC-1 fails in another suite'
);
reset role;
set local role service_role;
select public.record_report('acme', 'e2e', pg_temp.run(1002), pg_temp.report(
  '<testcase name="SPEC-1/AC-1 in the browser"/>'
));
reset role;
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);
select results_eq(
  'select * from pg_temp.proofs(1) where criterion = 1',
  $$values (1, 'proven')$$,
  'A run sent again replaces what it said'
);
select is(
  (select count(*) from public.latest_claims where suite = 'e2e'),
  1::bigint,
  'without counting its tests twice'
);

-- Rewording a criterion its tests name makes it unproven until a member confirms its tests.
select lives_ok(
  $$update public.criteria set text = 'Retries once after 60 seconds' where number = 1$$,
  'A member rewords AC-1'
);
select results_eq(
  'select * from pg_temp.proofs(1) where criterion = 1',
  $$values (1, 'unproven')$$,
  'which its tests no longer prove'
);
select lives_ok(
  $$update public.criteria set text = 'Shows the retry on the invoice' where number = 4$$,
  'Rewording AC-4, which no test names'
);
select is(
  (select suspect_since from public.criteria where number = 4),
  null,
  'leaves nothing to confirm'
);
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);
select throws_ok(
  $$select public.confirm_criterion((select id from public.criteria where number = 1))$$,
  '42501', null, 'A viewer can''t confirm its tests'
);
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);
select lives_ok(
  $$select public.confirm_criterion((select id from public.criteria where number = 1))$$,
  'A member confirms them'
);
select results_eq(
  'select * from pg_temp.proofs(1) where criterion = 1',
  $$values (1, 'proven')$$,
  'and they prove it again'
);
select is(
  (select changes ? 'suspect_since' from public.events where subject_type = 'criterion' order by id desc limit 1),
  true,
  'The history records the confirmation'
);

-- The branch decides which reports count.
update public.repositories set branch = 'release';
select is((select branch from public.repositories), 'main', 'A member can''t change the branch');
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);
update public.repositories set branch = 'release';
select results_eq(
  'select count(*) from pg_temp.proofs(1) where state = ''unproven''',
  $$values (4::bigint)$$,
  'An owner moves it to another branch, whose runs haven''t reported'
);
update public.repositories set branch = 'main';

-- Only the last 20 reports of a suite are kept, and a repository sends at most 120 an hour.
reset role;
set local role service_role;
select public.record_report('acme', 'unit', pg_temp.run(2000 + n), pg_temp.report('<testcase name="test_SPEC_1_AC_1"/>'))
from generate_series(1, 21) as n;
select is(
  (select count(*) from public.test_reports where suite = 'unit'),
  20::bigint,
  'A suite keeps its last 20 reports'
);
reset role;
select set_config('test.left', (120 - (select sum(sent) from private.report_hours))::text, true);
set local role service_role;
select public.record_report('acme', 'load', pg_temp.run(3000 + n), pg_temp.report('<testcase name="a"/>'))
from generate_series(1, current_setting('test.left')::integer) as n;
select throws_ok(
  $$select public.record_report('acme', 'load', pg_temp.run(4000), pg_temp.report('<testcase name="a"/>'))$$,
  '54000', 'A repository can send at most 120 reports an hour', 'and a repository sends at most 120 an hour'
);

-- Removing a repository removes what it proved.
reset role;
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);
select lives_ok($$delete from public.repositories$$, 'An owner removes the repository');
select is((select count(*) from public.test_reports), 0::bigint, 'with its reports');
select results_eq(
  'select count(*) from pg_temp.proofs(1) where state = ''unproven''',
  $$values (4::bigint)$$,
  'so nothing is proven any more'
);

select * from finish();
rollback;
