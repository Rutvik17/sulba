-- A member starts one of Sulba's agents on a request within the workspace's monthly limit, which
-- only Sulba sets; the Worker alone records the run's session and ends it; Intake's questions are
-- asked as the person's agent, by name; and only the workspace's members see its runs.
begin;
select plan(30);

insert into auth.users (id, email, raw_user_meta_data) values
  ('a0000000-0000-4000-8000-000000000001', 'ada@example.com', '{"full_name": "Ada Lovelace"}'),
  ('b0000000-0000-4000-8000-000000000002', 'ben@example.com', '{"name": "Ben"}'),
  ('c0000000-0000-4000-8000-000000000003', 'cy@example.com', '{"name": "Cy"}'),
  ('d0000000-0000-4000-8000-000000000004', 'di@example.com', '{"name": "Di"}');

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
create function pg_temp.as_worker() returns void language sql as $$
  select set_config('request.jwt.claims', '{"role": "service_role"}', true)
$$;
create function pg_temp.run(n integer) returns uuid language sql as $$
  select current_setting('test.run' || n)::uuid
$$;

select ok(
  not has_function_privilege('anon', 'public.begin_agent_run(uuid, public.agent_role)', 'execute')
    and not has_function_privilege('anon', 'public.agent_spending(uuid)', 'execute'),
  'Visitors can''t start agents or read what they spent'
);
select ok(
  not has_function_privilege('authenticated', 'public.agent_run_brief(uuid)', 'execute')
    and not has_function_privilege('authenticated', 'public.agent_run_started(uuid, text, integer)', 'execute')
    and not has_function_privilege('authenticated', 'public.end_agent_run(uuid, public.agent_run_status, integer, text)', 'execute')
    and not has_function_privilege('authenticated', 'public.end_intake_run(uuid, text[], integer)', 'execute')
    and not has_function_privilege('authenticated', 'public.managed_agent(text)', 'execute')
    and not has_function_privilege('authenticated', 'public.save_managed_agent(text, text, text, integer)', 'execute'),
  'Only the Worker records a run''s session, ends it and keeps Sulba''s agents'
);

-- Ada's workspace, with Ben as a member and Cy as a viewer, and Di's own workspace.
set local role authenticated;
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select set_config('test.acme', (select id::text from public.create_workspace('Acme', 'acme')), true);
select set_config('test.member', public.create_invitation(current_setting('test.acme')::uuid, 'member'), true);
select set_config('test.viewer', public.create_invitation(current_setting('test.acme')::uuid, 'viewer'), true);
select public.create_request(current_setting('test.acme')::uuid, 'A booking app', 'Members book classes.');
select public.create_request(current_setting('test.acme')::uuid, 'Class reminders');
select set_config('test.request', (select id::text from public.requests where number = 1), true);
select set_config('test.second', (select id::text from public.requests where number = 2), true);
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select public.accept_invitation(current_setting('test.member'));
select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select public.accept_invitation(current_setting('test.viewer'));
select pg_temp.as_person('d0000000-0000-4000-8000-000000000004');
select public.create_workspace('Di Co', 'di-co');

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select is(
  (select agent_limit_cents from public.workspaces where slug = 'acme'), 0,
  'A workspace starts with no allowance for Sulba''s agents'
);
select throws_ok(
  $$update public.workspaces set agent_limit_cents = 5000 where slug = 'acme'$$,
  '42501', 'permission denied for table workspaces', 'and its owner can''t give it one'
);
select throws_ok(
  $$select public.begin_agent_run(current_setting('test.request')::uuid, 'intake')$$,
  '54000', 'This workspace has used its agent allowance for this month',
  'No run starts without an allowance'
);

reset role;
update public.workspaces set agent_limit_cents = 250 where slug = 'acme';
set local role authenticated;

select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select throws_ok(
  $$select public.begin_agent_run(current_setting('test.request')::uuid, 'intake')$$,
  '42501', 'Only members can start Sulba''s agents', 'A viewer can''t start an agent'
);
select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select throws_ok(
  $$select public.begin_agent_run(current_setting('test.request')::uuid, 'intake')$$,
  '42501', 'An agent can''t start Sulba''s agents. A person does that in Sulba',
  'nor can a member''s agent'
);

select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select lives_ok(
  $$select set_config('test.run1', public.begin_agent_run(current_setting('test.request')::uuid, 'intake')::text, true)$$,
  'A member starts Intake on a request'
);
select results_eq(
  $$select role::text, status::text, budget_cents, cost_cents, started_by::text, session_id from public.agent_runs$$,
  $$values ('intake', 'running', 100, 0, 'b0000000-0000-4000-8000-000000000002', null::text)$$,
  'The run is Intake''s, running, with the role''s cap as its budget'
);
select results_eq(
  $$select * from public.agent_spending(current_setting('test.acme')::uuid)$$,
  $$values (250, 0, 100)$$,
  'Its budget is set aside from the month''s limit while it runs'
);
select throws_ok(
  $$select public.begin_agent_run(current_setting('test.request')::uuid, 'intake')$$,
  '23505', 'Sulba Intake is already working on this request', 'One Intake runs on a request at a time'
);
select lives_ok(
  $$select set_config('test.run2', public.begin_agent_run(current_setting('test.second')::uuid, 'intake')::text, true)$$,
  'Another request can have its own'
);
select is(
  (select budget_cents from public.agent_runs where id = pg_temp.run(2)), 100,
  'which sets aside another 100 cents'
);
select throws_ok(
  $$update public.agent_runs set cost_cents = 0$$,
  '42501', 'permission denied for table agent_runs', 'No one changes a run directly'
);

-- The Worker starts the first run's session, and Intake comes back with two questions.
reset role;
set local role service_role;
select pg_temp.as_worker();
select results_eq(
  $$select public.agent_run_brief(pg_temp.run(1)) #>> '{request,title}', public.agent_run_brief(pg_temp.run(1)) ->> 'budget_cents'$$,
  $$values ('A booking app', '100')$$,
  'The Worker reads the run''s request and budget'
);
select public.agent_run_started(pg_temp.run(1), 'sesn_01', 3);
select results_eq(
  $$select session_id, agent_version from public.agent_runs where id = pg_temp.run(1)$$,
  $$values ('sesn_01', 3)$$,
  'and records its session and the agent''s version'
);
select is(
  public.end_intake_run(pg_temp.run(1), array['Do members pay when they book?', 'Which classes are bookable?'], 37),
  true,
  'The Worker ends the run with its questions'
);
select results_eq(
  $$select text, asked_by::text, asked_by_agent from public.questions order by asked_at, text$$,
  $$values ('Do members pay when they book?', 'b0000000-0000-4000-8000-000000000002', 'Sulba Intake'),
    ('Which classes are bookable?', 'b0000000-0000-4000-8000-000000000002', 'Sulba Intake')$$,
  'Each question is asked for the person who started the run, by Sulba Intake'
);
select results_eq(
  $$select distinct actor_kind::text, actor_id::text, actor_agent from public.events where subject_type = 'question'$$,
  $$values ('agent', 'b0000000-0000-4000-8000-000000000002', 'Sulba Intake')$$,
  'and the history names the agent'
);
select results_eq(
  $$select status::text, cost_cents, note, ended_at is not null from public.agent_runs where id = pg_temp.run(1)$$,
  $$values ('done', 37, 'Asked 2 questions.', true)$$,
  'The run is done, with what it cost'
);
select is(
  (select current_setting('request.jwt.claims', true)::jsonb ->> 'sulba_agent'), null,
  'and the agent acts only while the Worker writes its work'
);
select is(
  public.end_intake_run(pg_temp.run(1), array['Asked twice?'], 99), false,
  'Ending a run again changes nothing'
);
select is((select count(*) from public.questions), 2::bigint, 'and asks nothing more');
select throws_ok(
  $$select public.end_agent_run(pg_temp.run(2), 'running', 0)$$,
  '22023', 'A run ends as done, failed or stopped', 'A run can''t end as running'
);
select is(
  public.end_agent_run(pg_temp.run(2), 'stopped', 100, 'Reached its budget.'), true,
  'The Worker ends a run that reached its budget'
);

reset role;
set local role authenticated;
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select results_eq(
  $$select * from public.agent_spending(current_setting('test.acme')::uuid)$$,
  $$values (250, 137, 0)$$,
  'The month''s spending is what the ended runs cost'
);
select lives_ok(
  $$select set_config('test.run3', public.begin_agent_run(current_setting('test.second')::uuid, 'intake')::text, true)$$,
  'A new run starts with what is left'
);
select is(
  (select budget_cents from public.agent_runs where id = pg_temp.run(3)), 100,
  'which is the role''s cap while more than that is left'
);

select pg_temp.as_person('d0000000-0000-4000-8000-000000000004');
select is((select count(*) from public.agent_runs), 0::bigint, 'No one else sees a workspace''s runs');
select is(
  (select count(*) from public.agent_spending(current_setting('test.acme')::uuid)), 0::bigint,
  'nor what it spent'
);

select * from finish();
rollback;
