-- An agent acts for its person within their role on specs and criteria, its changes are named
-- as its own in the history, and the decisions that govern a workspace stay with people.
begin;
select plan(30);

insert into auth.users (id, email, raw_user_meta_data) values
  ('a0000000-0000-4000-8000-000000000001', 'ada@example.com', '{"full_name": "Ada Lovelace"}'),
  ('b0000000-0000-4000-8000-000000000002', 'ben@example.com', '{"name": "Ben"}');

-- Claude Code, as it registers itself with the OAuth server.
insert into auth.oauth_clients (
  id, registration_type, redirect_uris, grant_types, client_name, client_type, token_endpoint_auth_method
) values (
  'e0000000-0000-4000-8000-000000000005', 'dynamic', 'http://127.0.0.1:9999/callback',
  'authorization_code,refresh_token', 'Claude Code', 'public', 'none'
);

create function pg_temp.as_person(person text) returns void language sql as $$
  select set_config('request.jwt.claims', json_build_object('sub', person, 'role', 'authenticated')::text, true)
$$;
-- Each person's agent has a session of its own, as the OAuth server makes when its person allows
-- it, and its token names that session.
insert into auth.sessions (id, user_id, oauth_client_id) values
  ('d0000000-0000-4000-8000-000000000001', 'a0000000-0000-4000-8000-000000000001', 'e0000000-0000-4000-8000-000000000005'),
  ('d0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000002', 'e0000000-0000-4000-8000-000000000005');
create function pg_temp.as_agent(person text) returns void language sql as $$
  select set_config('request.jwt.claims', json_build_object(
    'sub', person, 'role', 'authenticated', 'client_id', 'e0000000-0000-4000-8000-000000000005',
    'session_id', 'd0000000-0000-4000-8000-00000000000' || right(person, 1)
  )::text, true)
$$;

select ok(
  not has_function_privilege('authenticated', 'private.by_agent()', 'execute')
    and not has_function_privilege('authenticated', 'private.connected()', 'execute'),
  'Signed-in people can''t call the checks themselves'
);

-- Ada's workspace, with Ben as a member.
set local role authenticated;
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select set_config('test.acme', (select id::text from public.create_workspace('Acme', 'acme')), true);
select set_config('test.link', public.create_invitation(current_setting('test.acme')::uuid, 'member'), true);
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select public.accept_invitation(current_setting('test.link'));

-- Ben's agent works on specs.
select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select is(
  public.create_spec(current_setting('test.acme')::uuid, 'Retry failed payments', array['Retries once after 30 seconds']),
  1,
  'An agent writes a spec'
);
select set_config('test.spec', (select id::text from public.specs where number = 1), true);
select is(public.add_criterion(current_setting('test.spec')::uuid, 'Keeps the idempotency key'), 2, 'and adds a criterion');
select set_config('test.criterion', (select id::text from public.criteria where number = 1), true);
select throws_ok(
  $$select public.close_account()$$, '42501', 'An agent can''t close an account. Its person does that in Sulba',
  'An agent can''t close its person''s account'
);
select lives_ok(
  $$update public.criteria set text = 'Retries once after 60 seconds' where id = current_setting('test.criterion')::uuid$$,
  'rewords one'
);
select lives_ok(
  $$update public.specs set body = 'Payments fail for many reasons.' where id = current_setting('test.spec')::uuid$$,
  'writes its text'
);
select lives_ok(
  $$update public.specs set status = 'in_review' where id = current_setting('test.spec')::uuid$$,
  'and puts it in review'
);
select results_eq(
  $$select actor_kind::text, actor_id, actor_client, actor_agent from public.events where action = 'spec.created'$$,
  $$values ('agent', 'b0000000-0000-4000-8000-000000000002'::uuid, 'e0000000-0000-4000-8000-000000000005', 'Claude Code')$$,
  'The history names the agent and the person it acts for'
);

-- The decisions about a spec are people's.
select throws_ok(
  $$update public.specs set status = 'approved' where id = current_setting('test.spec')::uuid$$,
  '42501', 'An agent can''t approve, abandon or supersede a spec. A person in the workspace does that',
  'An agent can''t approve a spec'
);
select throws_ok(
  $$update public.specs set status = 'abandoned' where id = current_setting('test.spec')::uuid$$,
  '42501', null, 'or abandon it'
);
select throws_ok(
  $$update public.specs set status = 'superseded' where id = current_setting('test.spec')::uuid$$,
  '42501', null, 'or supersede it'
);
select lives_ok(
  $$update public.specs set status = 'implemented' where id = current_setting('test.spec')::uuid$$,
  'but marks it implemented'
);
select throws_ok(
  $$delete from public.criteria where id = current_setting('test.criterion')::uuid$$,
  '42501', 'An agent can''t remove a criterion. A person does that in Sulba',
  'An agent can''t remove a criterion'
);
reset role;
update public.criteria set suspect_since = now() where id = current_setting('test.criterion')::uuid;
set local role authenticated;
select throws_ok(
  $$select public.confirm_criterion(current_setting('test.criterion')::uuid)$$,
  '42501', null, 'or confirm a reworded criterion''s tests'
);

-- Ada's agent can't do what only her role lets her do in the workspace.
select pg_temp.as_agent('a0000000-0000-4000-8000-000000000001');
select throws_ok(
  $$update public.workspaces set name = 'Acme Co' where id = current_setting('test.acme')::uuid$$,
  '42501', 'An agent can''t create, rename or delete a workspace. A person does that in Sulba',
  'An owner''s agent can''t rename the workspace'
);
select throws_ok($$select public.create_workspace('Agents', 'agents')$$, '42501', null, 'or create one');
select throws_ok(
  $$select public.delete_workspace(current_setting('test.acme')::uuid)$$, '42501', null, 'or delete one'
);
select throws_ok(
  $$select public.create_invitation(current_setting('test.acme')::uuid, 'viewer')$$, '42501', null, 'or invite anyone'
);
select throws_ok(
  $$select public.set_member_role(current_setting('test.acme')::uuid, 'b0000000-0000-4000-8000-000000000002', 'admin')$$,
  '42501', null, 'or change a role'
);
select throws_ok(
  $$select public.remove_member(current_setting('test.acme')::uuid, 'b0000000-0000-4000-8000-000000000002')$$,
  '42501', null, 'or remove a member'
);
select throws_ok(
  $$select public.add_repository(current_setting('test.acme')::uuid, 'acme-co/payments')$$,
  '42501', null, 'or add a repository'
);
select is(
  (select count(*) from public.members where workspace_id = current_setting('test.acme')::uuid),
  2::bigint,
  'and the workspace is as it was'
);

-- Ada herself decides.
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select lives_ok(
  $$update public.specs set status = 'approved' where id = current_setting('test.spec')::uuid$$,
  'A person approves the spec'
);
select lives_ok(
  $$select public.confirm_criterion(current_setting('test.criterion')::uuid)$$,
  'confirms the criterion''s tests'
);
select results_eq(
  $$select actor_kind::text, actor_agent from public.events where action = 'spec.updated' order by id desc limit 1$$,
  $$values ('person', null::text)$$,
  'and the history names her alone'
);
select throws_ok($$select public.create_workspace('OAuth', 'oauth')$$, '23514', null, 'No workspace takes the consent page''s address');

-- Ben disconnects his agent, which ends its session; its token still verifies until it expires,
-- but it reaches nothing.
reset role;
delete from auth.sessions where id = 'd0000000-0000-4000-8000-000000000002';
set local role authenticated;
select pg_temp.as_agent('b0000000-0000-4000-8000-000000000002');
select is_empty($$select from public.workspaces$$, 'A disconnected agent sees no workspace');
select is_empty($$select from public.specs$$, 'or spec');
select throws_ok(
  $$select public.create_spec(current_setting('test.acme')::uuid, 'Refunds', array['A refund is logged'])$$,
  '42501', 'Only members can write specs', 'and can''t write one'
);
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select isnt_empty($$select from public.specs$$, 'while Ben, signed in himself, still sees the specs');

select * from finish();
rollback;
