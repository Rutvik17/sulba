-- A person approves a request's release once every spec drafted from it is approved and every one
-- of their criteria is proven; the release keeps what was proven; agents and viewers can't approve
-- one; and only the workspace's members see it.
begin;
select plan(17);

insert into auth.users (id, email, raw_user_meta_data) values
  ('a0000000-0000-4000-8000-000000000001', 'ada@example.com', '{"full_name": "Ada Lovelace"}'),
  ('b0000000-0000-4000-8000-000000000002', 'ben@example.com', '{"name": "Ben"}'),
  ('c0000000-0000-4000-8000-000000000003', 'cy@example.com', '{"name": "Cy"}'),
  ('d0000000-0000-4000-8000-000000000004', 'dee@example.com', '{"name": "Dee"}');

insert into auth.oauth_clients (
  id, registration_type, redirect_uris, grant_types, client_name, client_type, token_endpoint_auth_method
) values (
  'e0000000-0000-4000-8000-000000000005', 'dynamic', 'http://127.0.0.1:9999/callback',
  'authorization_code,refresh_token', 'Claude Code', 'public', 'none'
);
insert into auth.sessions (id, user_id, oauth_client_id) values
  ('d0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000002', 'e0000000-0000-4000-8000-000000000005');

create function pg_temp.as_person(person text) returns void language sql as $$
  select set_config('request.jwt.claims', json_build_object('sub', person, 'role', 'authenticated')::text, true)
$$;
create function pg_temp.as_agent(person text) returns void language sql as $$
  select set_config('request.jwt.claims', json_build_object(
    'sub', person, 'role', 'authenticated', 'client_id', 'e0000000-0000-4000-8000-000000000005',
    'session_id', 'd0000000-0000-4000-8000-00000000000' || right(person, 1)
  )::text, true)
$$;
-- A run's claims as the Worker passes them, and a JUnit XML report of the given test cases.
create function pg_temp.run(id integer) returns jsonb language sql as $$
  select jsonb_build_object(
    'repository', 'acme-co/booking', 'repository_id', '101', 'repository_owner_id', '55',
    'ref', 'refs/heads/main', 'sha', repeat('a', 40), 'run_id', id::text, 'run_attempt', '1',
    'workflow', 'CI'
  )
$$;
create function pg_temp.report(cases text) returns text[] language sql as $$
  select array['<?xml version="1.0" encoding="UTF-8"?><testsuites><testsuite name="tests">' || cases || '</testsuite></testsuites>']
$$;
create function pg_temp.request(number integer) returns uuid language sql as $$
  select id from public.requests where workspace_id = current_setting('test.acme')::uuid and number = $1
$$;

select ok(
  not has_function_privilege('anon', 'public.approve_release(uuid, text)', 'execute'),
  'Visitors can''t approve a release'
);

-- Ada's workspace, with Ben as a member and Cy as a viewer, its repository, and a request with a
-- spec drafted from it; and Dee's own workspace.
set local role authenticated;
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select set_config('test.acme', (select id::text from public.create_workspace('Acme', 'acme')), true);
select set_config('test.member', public.create_invitation(current_setting('test.acme')::uuid, 'member'), true);
select set_config('test.viewer', public.create_invitation(current_setting('test.acme')::uuid, 'viewer'), true);
select public.add_repository(current_setting('test.acme')::uuid, 'acme-co/booking');
select public.create_request(current_setting('test.acme')::uuid, 'A booking app');
select public.create_request(current_setting('test.acme')::uuid, 'Class reminders');
select public.create_spec(
  current_setting('test.acme')::uuid, 'Book a class',
  array['A member books a class', 'A full class refuses a booking'], pg_temp.request(1)
);
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select public.accept_invitation(current_setting('test.member'));
select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select public.accept_invitation(current_setting('test.viewer'));
select pg_temp.as_person('d0000000-0000-4000-8000-000000000004');
select public.create_workspace('Delta', 'delta');

select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select throws_ok(
  $$select public.approve_release(pg_temp.request(1))$$,
  '42501', 'Only members can approve a release', 'A viewer can''t approve a release'
);
select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select throws_ok(
  $$select public.approve_release(pg_temp.request(1))$$,
  '42501', 'An agent can''t approve a release. A person does that in Sulba',
  'An agent can''t approve a release'
);

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select throws_ok(
  $$select public.approve_release(pg_temp.request(2))$$,
  '23514', 'No spec has been drafted from this request yet', 'A request with no specs has nothing to release'
);
select throws_ok(
  $$select public.approve_release(pg_temp.request(1))$$,
  '23514', 'SPEC-1 is draft. Every spec is approved before its release',
  'A release waits for every spec to be approved'
);
update public.specs set status = 'approved' where number = 1;
select throws_ok(
  $$select public.approve_release(pg_temp.request(1))$$,
  '23514', 'SPEC-1/AC-1 isn''t proven. Every criterion is proven by the tests before its release',
  'and for every criterion to be proven'
);

-- The repository's CI proves both criteria.
reset role;
set local role service_role;
select set_config('request.jwt.claims', '{"role": "service_role"}', true);
select public.record_report('acme', 'unit', pg_temp.run(1000), pg_temp.report($$
  <testcase classname="tests.test_booking" name="test_SPEC_1_AC_1_books"/>
  <testcase classname="tests.test_booking" name="test_SPEC_1_AC_2_refuses_when_full"/>
$$));
reset role;
set local role authenticated;

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select is(
  public.approve_release(pg_temp.request(1), '  First release for the front desk.  '),
  1,
  'Once they are, Ada approves release 1'
);
select results_eq(
  $$select number, note, approved_by::text, jsonb_array_length(snapshot) from public.releases$$,
  $$values (1, 'First release for the front desk.', 'a0000000-0000-4000-8000-000000000001', 1)$$,
  'It keeps its note, trimmed, who approved it, and the one spec'
);
select is(
  (select snapshot -> 0 -> 'criteria' from public.releases where number = 1),
  '[{"number": 1, "text": "A member books a class", "tests": 1}, {"number": 2, "text": "A full class refuses a booking", "tests": 1}]'::jsonb,
  'and each criterion with the tests that proved it'
);
select is(
  (select changes -> 'snapshot' from public.events where action = 'release.created'),
  'null'::jsonb,
  'The history records the release without copying what it holds'
);

-- A second spec drafted from the request holds the next release back until it's proven or set
-- aside.
select public.create_spec(current_setting('test.acme')::uuid, 'Cancel a booking', '{}', pg_temp.request(1));
update public.specs set status = 'approved' where number = 2;
select throws_ok(
  $$select public.approve_release(pg_temp.request(1))$$,
  '23514', 'SPEC-2 has no criteria. Every criterion is proven by the tests before its release',
  'A spec with no criteria holds a release back'
);
update public.specs set status = 'abandoned' where number = 2;
select is(public.approve_release(pg_temp.request(1)), 2, 'An abandoned spec is left out, and the next release is 2');

select throws_ok(
  $$insert into public.releases (workspace_id, request_id, number, snapshot)
    values (current_setting('test.acme')::uuid, pg_temp.request(1), 9, '[]')$$,
  '42501', 'permission denied for table releases', 'A release is made only by approving it'
);
select throws_ok(
  $$delete from public.releases$$,
  '42501', 'permission denied for table releases', 'and never deleted'
);

update public.requests set status = 'closed' where number = 1;
select throws_ok(
  $$select public.approve_release(pg_temp.request(1))$$,
  '23514', 'This request is closed, so it has nothing to release', 'A closed request has nothing to release'
);

select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select is((select count(*) from public.releases), 2::bigint, 'Members see the workspace''s releases');
select pg_temp.as_person('d0000000-0000-4000-8000-000000000004');
select is((select count(*) from public.releases), 0::bigint, 'No one else sees them');

select * from finish();
rollback;
