-- Tasks are written only from an approved spec; one taker at a time; an agent takes, blocks and
-- hands in a task for its person, with a pull request in one of the workspace's repositories, but
-- only people mark it done, cancel it or open it again; and only the workspace's members see it.
begin;
select plan(35);

insert into auth.users (id, email, raw_user_meta_data) values
  ('a0000000-0000-4000-8000-000000000001', 'ada@example.com', '{"full_name": "Ada Lovelace"}'),
  ('b0000000-0000-4000-8000-000000000002', 'ben@example.com', '{"name": "Ben"}'),
  ('c0000000-0000-4000-8000-000000000003', 'cy@example.com', '{"name": "Cy"}');

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
create function pg_temp.task(number integer) returns uuid language sql as $$
  select id from public.tasks where workspace_id = current_setting('test.acme')::uuid and number = $1
$$;

select ok(
  not has_function_privilege('anon', 'public.create_task(uuid, text, public.task_role, text, integer[])', 'execute')
    and not has_function_privilege('anon', 'public.update_task(uuid, public.task_status, text, text)', 'execute'),
  'Visitors can''t call the task functions'
);

-- Ada's workspace, with Ben as a member and Cy as a viewer, a spec with two criteria, and Cy's
-- own workspace with an approved spec of its own.
set local role authenticated;
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select set_config('test.acme', (select id::text from public.create_workspace('Acme', 'acme')), true);
select set_config('test.member', public.create_invitation(current_setting('test.acme')::uuid, 'member'), true);
select set_config('test.viewer', public.create_invitation(current_setting('test.acme')::uuid, 'viewer'), true);
select public.create_spec(
  current_setting('test.acme')::uuid, 'Book a class',
  array['A member books a class', 'A full class refuses a booking']
);
select set_config(
  'test.spec',
  (select id::text from public.specs where workspace_id = current_setting('test.acme')::uuid),
  true
);
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select public.accept_invitation(current_setting('test.member'));
select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select public.accept_invitation(current_setting('test.viewer'));
select set_config('test.cyco', (select id::text from public.create_workspace('Cy Co', 'cy-co')), true);
select public.create_spec(current_setting('test.cyco')::uuid, 'A shop');
update public.specs set status = 'approved' where workspace_id = current_setting('test.cyco')::uuid;
select public.create_task(
  (select id from public.specs where workspace_id = current_setting('test.cyco')::uuid), 'Build the shop'
);

select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select throws_ok(
  $$select public.create_task(current_setting('test.spec')::uuid, 'Build the booking API')$$,
  '23514', 'This spec is draft. Tasks are written once it''s approved',
  'No task is written from a spec no one approved'
);

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
update public.specs set status = 'approved' where id = current_setting('test.spec')::uuid;

select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select throws_ok(
  $$select public.create_task(current_setting('test.spec')::uuid, 'Build the booking API')$$,
  '42501', 'Only members can write tasks', 'A viewer can''t write a task'
);

select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select throws_ok(
  $$select public.create_task(
    (select id from public.specs where workspace_id = current_setting('test.cyco')::uuid), 'Take it'
  )$$,
  '42501', 'Only members can write tasks', 'An agent can''t write a task for another workspace''s spec'
);
select throws_ok(
  $$select public.create_task(current_setting('test.spec')::uuid, 'Build it', 'build', '', '{1,3}')$$,
  'P0002', 'This spec has no AC-3', 'A task covers only its spec''s criteria'
);
select is(
  public.create_task(
    current_setting('test.spec')::uuid, '  Build the booking API  ', 'build',
    'Add POST /bookings.', '{1,2}'
  ),
  1,
  'Ben''s agent writes a task from the approved spec, which is TASK-1'
);
select results_eq(
  $$select title, role::text, status::text, body, created_by::text, created_by_agent
    from public.tasks where id = pg_temp.task(1)$$,
  $$values ('Build the booking API', 'build', 'open', 'Add POST /bookings.',
    'b0000000-0000-4000-8000-000000000002', 'Claude Code')$$,
  'It keeps its title, trimmed, its role and instructions, and who wrote it, and is open'
);
select is(
  (select count(*) from public.task_criteria where task_id = pg_temp.task(1)),
  2::bigint,
  'It covers the criteria it names'
);
select ok(
  exists (
    select from public.events
    where action = 'task.created' and actor_kind = 'agent' and subject_id = pg_temp.task(1)::text
      and spec_id = current_setting('test.spec')::uuid
  ),
  'The spec''s history says an agent wrote it'
);

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select is(
  public.create_task(current_setting('test.spec')::uuid, 'Test the booking API', 'test'),
  2,
  'A person writes the next task, TASK-2'
);

select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select throws_ok(
  $$select public.update_task(pg_temp.task(1), 'blocked', 'No database')$$,
  '23514', 'TASK-1 is open. Take it first', 'An open task is taken before anything else'
);
select lives_ok(
  $$select public.update_task(pg_temp.task(1), 'in_progress')$$,
  'Ben''s agent takes TASK-1'
);
select results_eq(
  $$select status::text, taken_by::text, taken_by_agent from public.tasks where id = pg_temp.task(1)$$,
  $$values ('in_progress', 'b0000000-0000-4000-8000-000000000002', 'Claude Code')$$,
  'It''s in progress, taken by the agent for Ben'
);

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select throws_ok(
  $$select public.update_task(pg_temp.task(1), 'in_progress')$$,
  '23514', 'TASK-1 is already in progress', 'No one takes a task someone has'
);
select lives_ok($$select public.update_task(pg_temp.task(2), 'in_progress')$$, 'Ada takes TASK-2');

select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select throws_ok(
  $$select public.update_task(pg_temp.task(1), 'blocked', 'Stuck')$$,
  '42501', 'Only members can work on tasks', 'A viewer can''t move a task'
);

select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select throws_ok(
  $$select public.update_task(pg_temp.task(2), 'blocked', 'Stuck')$$,
  '42501', 'TASK-2 is taken by someone else', 'An agent moves only its own person''s tasks'
);
select throws_ok(
  $$select public.update_task(pg_temp.task(1), 'blocked')$$,
  '23514', 'Say what blocks it', 'A blocked task says why'
);
select lives_ok(
  $$select public.update_task(pg_temp.task(1), 'blocked', '  Which payment provider?  ')$$,
  'The agent blocks its task, saying why'
);
select is(
  (select note from public.tasks where id = pg_temp.task(1)),
  'Which payment provider?',
  'The task keeps the reason, trimmed'
);
select throws_ok(
  $$select public.update_task(pg_temp.task(1), 'in_review')$$,
  '23514', 'Name the pull request that holds the work', 'A task is handed in with its pull request'
);
select throws_ok(
  $$select public.update_task(pg_temp.task(1), 'in_review', null, 'https://example.com/pull/1')$$,
  '22023', 'A pull request''s address looks like https://github.com/owner/repo/pull/12',
  'A pull request is on GitHub'
);
select throws_ok(
  $$select public.update_task(pg_temp.task(1), 'in_review', null, 'https://github.com/acme-co/booking/pull/12')$$,
  '23514', 'acme-co/booking isn''t one of this workspace''s repositories',
  'A pull request is in one of the workspace''s repositories'
);

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select public.add_repository(current_setting('test.acme')::uuid, 'Acme-Co/Booking');

select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select lives_ok(
  $$select public.update_task(
    pg_temp.task(1), 'in_review', 'Adds POST /bookings.', 'https://github.com/acme-co/booking/pull/12'
  )$$,
  'The agent hands its task in with a pull request in the workspace''s repository'
);
select results_eq(
  $$select status::text, note, pull_request from public.tasks where id = pg_temp.task(1)$$,
  $$values ('in_review', 'Adds POST /bookings.', 'https://github.com/acme-co/booking/pull/12')$$,
  'It''s in review, with the pull request and what the agent said'
);
select throws_ok(
  $$select public.update_task(pg_temp.task(1), 'done')$$,
  '42501', 'An agent can''t mark a task done or cancel it. A person does that in Sulba',
  'An agent can''t mark its own work done'
);

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select lives_ok($$select public.update_task(pg_temp.task(1), 'done')$$, 'Ada marks TASK-1 done');

select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select throws_ok(
  $$select public.update_task(pg_temp.task(1), 'open')$$,
  '42501', 'An agent can''t open a done task again. A person does that in Sulba',
  'An agent can''t open a finished task again'
);

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select lives_ok($$select public.update_task(pg_temp.task(2), 'open')$$, 'Ada releases TASK-2');
select results_eq(
  $$select status::text, taken_by, taken_at from public.tasks where id = pg_temp.task(2)$$,
  $$values ('open', null::uuid, null::timestamptz)$$,
  'A released task is open again, with no taker'
);
select throws_ok(
  $$update public.tasks set status = 'done' where id = pg_temp.task(2)$$,
  '42501', 'permission denied for table tasks', 'A task''s status changes only through update_task'
);
select throws_ok(
  $$delete from public.tasks where id = pg_temp.task(2)$$,
  '42501', 'permission denied for table tasks', 'A task is canceled, not deleted'
);

select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
update public.tasks set title = 'Test booking a class' where id = pg_temp.task(2);
select is(
  (select title from public.tasks where id = pg_temp.task(2)),
  'Test booking a class',
  'Members and their agents edit a task''s title'
);

select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
update public.tasks set title = 'Renamed' where id = pg_temp.task(2);
select is(
  (select title from public.tasks where id = pg_temp.task(2)),
  'Test booking a class',
  'A viewer reads tasks but changes nothing'
);

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select is(
  (select count(*) from public.tasks where workspace_id = current_setting('test.cyco')::uuid),
  0::bigint,
  'No one sees another workspace''s tasks'
);

select * from finish();
rollback;
