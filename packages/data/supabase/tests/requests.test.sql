-- A member writes a request and its number is never given twice; an agent asks about it and drafts
-- specs from it; only people answer, change a request or decide it's planned or closed; and only
-- the workspace's members see it.
begin;
select plan(27);

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

select ok(
  not has_function_privilege('anon', 'public.create_request(uuid, text, text)', 'execute')
    and not has_function_privilege('anon', 'public.ask_question(uuid, text)', 'execute')
    and not has_function_privilege('anon', 'public.answer_question(uuid, text)', 'execute')
    and not has_function_privilege('anon', 'public.create_spec(uuid, text, text[], uuid)', 'execute'),
  'Visitors can''t call the request functions'
);

-- Ada's workspace, with Ben as a member and Cy as a viewer, and Cy's own workspace.
set local role authenticated;
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select set_config('test.acme', (select id::text from public.create_workspace('Acme', 'acme')), true);
select set_config('test.member', public.create_invitation(current_setting('test.acme')::uuid, 'member'), true);
select set_config('test.viewer', public.create_invitation(current_setting('test.acme')::uuid, 'viewer'), true);
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select public.accept_invitation(current_setting('test.member'));
select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select public.accept_invitation(current_setting('test.viewer'));
select set_config('test.cyco', (select id::text from public.create_workspace('Cy Co', 'cy-co')), true);
select public.create_request(current_setting('test.cyco')::uuid, 'A shop');
select set_config(
  'test.cyrequest',
  (select id::text from public.requests where workspace_id = current_setting('test.cyco')::uuid),
  true
);

select throws_ok(
  $$select public.create_request(current_setting('test.acme')::uuid, 'A booking app')$$,
  '42501', 'Only members can write requests', 'A viewer can''t write a request'
);

select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select is(
  public.create_request(current_setting('test.acme')::uuid, '  A booking app  ', 'Members book classes from their phones.'),
  1,
  'A member writes a request, which is REQ-1'
);
select set_config(
  'test.request',
  (select id::text from public.requests where workspace_id = current_setting('test.acme')::uuid and number = 1),
  true
);
select results_eq(
  $$select title, status::text, body, created_by::text from public.requests
    where workspace_id = current_setting('test.acme')::uuid$$,
  $$values ('A booking app', 'open', 'Members book classes from their phones.', 'a0000000-0000-4000-8000-000000000001')$$,
  'It keeps its title, trimmed, its text and its writer, and is open'
);
select is(public.create_request(current_setting('test.acme')::uuid, 'Class reminders'), 2, 'The next request is REQ-2');
select throws_ok(
  $$select public.create_request(current_setting('test.acme')::uuid, '')$$, '23514', null, 'A request has a title'
);
select results_eq(
  $$select action from public.events
    where subject_type = 'request' and workspace_id = current_setting('test.acme')::uuid order by id$$,
  $$values ('request.created'), ('request.created')$$,
  'The history records each request'
);

-- Ben's agent asks about it and drafts a spec from it.
select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select lives_ok(
  $$select public.ask_question(current_setting('test.request')::uuid, 'Do members pay when they book?')$$,
  'An agent asks about a request'
);
select set_config('test.question', (select id::text from public.questions), true);
select results_eq(
  $$select text, asked_by::text, asked_by_agent, answer from public.questions$$,
  $$values ('Do members pay when they book?', 'b0000000-0000-4000-8000-000000000002', 'Claude Code', null::text)$$,
  'The question names its asker and their agent, and waits for an answer'
);
select throws_ok(
  $$select public.answer_question(current_setting('test.question')::uuid, 'Yes')$$,
  '42501', 'An agent can''t answer a question. A person does that in Sulba',
  'An agent can''t answer a question'
);
select throws_ok(
  $$select public.create_request(current_setting('test.acme')::uuid, 'A payments page')$$,
  '42501', 'An agent can''t write or change a request. A person does that in Sulba',
  'An agent can''t write a request'
);
select throws_ok(
  $$update public.requests set status = 'planned' where workspace_id = current_setting('test.acme')::uuid and number = 1$$,
  '42501', 'An agent can''t write or change a request. A person does that in Sulba',
  'nor plan one'
);
select is(
  public.create_spec(
    current_setting('test.acme')::uuid, 'Book a class', array['A member books a class from the timetable'],
    current_setting('test.request')::uuid
  ),
  1,
  'An agent drafts a spec from a request'
);
select is(
  (select request_id::text from public.specs where number = 1),
  current_setting('test.request'),
  'and the spec names the request it came from'
);
select throws_ok(
  $$select public.create_spec(current_setting('test.acme')::uuid, 'Elsewhere', '{}', current_setting('test.cyrequest')::uuid)$$,
  'P0002', 'There''s no such request in this workspace',
  'A spec can''t name another workspace''s request'
);

-- Ada answers, and plans and closes the request.
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select lives_ok(
  $$select public.answer_question(current_setting('test.question')::uuid, '  Yes, by card.  ')$$,
  'A person answers a question'
);
select results_eq(
  $$select answer, answered_by::text, answered_at is not null from public.questions$$,
  $$values ('Yes, by card.', 'a0000000-0000-4000-8000-000000000001', true)$$,
  'The answer is trimmed and names who answered'
);
select lives_ok(
  $$update public.requests set status = 'planned', body = 'Members book and pay for classes.' where workspace_id = current_setting('test.acme')::uuid and number = 1$$,
  'A person plans a request and changes its text'
);
select throws_ok(
  $$select public.ask_question(current_setting('test.request')::uuid, 'Which card types?')$$,
  '23514', 'This request is planned. Questions are asked while it''s open',
  'Questions are asked only while a request is open'
);
update public.requests set status = 'closed' where workspace_id = current_setting('test.acme')::uuid and number = 1;
select throws_ok(
  $$select public.create_spec(current_setting('test.acme')::uuid, 'Pay by card', '{}', current_setting('test.request')::uuid)$$,
  '23514', 'This request is closed. Specs are drafted from open or planned requests',
  'No spec is drafted from a closed request'
);
select throws_ok(
  $$delete from public.requests where workspace_id = current_setting('test.acme')::uuid and number = 1$$, '42501', null, 'A request isn''t deleted'
);
select throws_ok(
  $$update public.questions set answer = 'No' where id = current_setting('test.question')::uuid$$,
  '42501', null, 'A question changes only through answer_question'
);

-- A viewer reads; others see nothing.
select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select is((select count(*) from public.requests where workspace_id = current_setting('test.acme')::uuid), 2::bigint, 'A viewer reads the requests');
select throws_ok(
  $$select public.answer_question(current_setting('test.question')::uuid, 'No')$$,
  '42501', 'Only members can answer a question', 'but can''t answer'
);
update public.requests set status = 'open' where workspace_id = current_setting('test.acme')::uuid;
select results_eq(
  $$select status::text from public.requests where number = 1 and workspace_id = current_setting('test.acme')::uuid$$,
  $$values ('closed')$$,
  'and an update a viewer makes changes nothing'
);
reset role;
insert into auth.users (id, email) values ('f0000000-0000-4000-8000-000000000006', 'eve@example.com');
set local role authenticated;
select pg_temp.as_person('f0000000-0000-4000-8000-000000000006');
select is_empty($$select from public.requests$$, 'Someone outside the workspace sees no requests');
select is_empty($$select from public.questions$$, 'nor their questions');

select * from finish();
rollback;
