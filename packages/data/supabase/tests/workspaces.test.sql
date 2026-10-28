-- A workspace's rows reach its members alone, each role can do what it says and no more, a
-- workspace always keeps an owner, and every change is logged.
begin;
select plan(68);

insert into auth.users (id, email, raw_user_meta_data) values
  ('a0000000-0000-4000-8000-000000000001', 'ada@example.com', '{"full_name": "Ada Lovelace"}'),
  ('b0000000-0000-4000-8000-000000000002', 'ben@example.com', '{"name": "Ben"}'),
  ('c0000000-0000-4000-8000-000000000003', 'cy@example.com', '{}');

select results_eq(
  'select name, email from public.people order by email',
  $$values ('Ada Lovelace', 'ada@example.com'), ('Ben', 'ben@example.com'), ('', 'cy@example.com')$$,
  'Each account has a person, named as their sign-in gave'
);

select schema_privs_are('access', 'anon', array[]::text[], 'Visitors can''t reach the access schema');
select schema_privs_are('access', 'authenticated', array['USAGE'], 'and signed-in people only call its functions');

-- Without signing in, nothing.
set local role anon;

select throws_ok('select * from public.workspaces', '42501', null, 'Visitors can''t read workspaces');
select throws_ok('select * from public.members', '42501', null, 'or members');
select throws_ok('select * from public.people', '42501', null, 'or people');
select throws_ok('select id from public.invitations', '42501', null, 'or invitations');
select throws_ok('select * from public.events', '42501', null, 'or the history');
select throws_ok(
  $$select public.create_workspace('Acme', 'acme')$$, '42501', null, 'Visitors can''t create a workspace'
);

-- Ada creates a workspace.
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);

select lives_ok(
  $$select set_config('test.acme', (select id::text from public.create_workspace(' Acme ', 'Acme')), true)$$,
  'A person creates a workspace'
);
select results_eq(
  'select name, slug from public.workspaces',
  $$values ('Acme', 'acme')$$,
  'with its name trimmed and its address in lowercase'
);
select results_eq(
  'select person_id, role from public.members',
  $$values ('a0000000-0000-4000-8000-000000000001'::uuid, 'owner'::public.workspace_role)$$,
  'and is its owner'
);
select results_eq(
  'select action, actor_kind, actor_id from public.events order by id',
  $$values
    ('workspace.created', 'person'::public.actor_kind, 'a0000000-0000-4000-8000-000000000001'::uuid),
    ('member.created', 'person'::public.actor_kind, 'a0000000-0000-4000-8000-000000000001'::uuid)$$,
  'Both are logged, as the person''s doing'
);

select throws_ok(
  $$select public.create_workspace('Acme two', 'acme')$$, '23505', null, 'An address is taken once'
);
select throws_ok($$select public.create_workspace('A', 'ab')$$, '23514', null, 'An address has 3 characters or more');
select throws_ok($$select public.create_workspace('A', 'a--b')$$, '23514', null, 'and no double hyphens');
select throws_ok($$select public.create_workspace('A', '-ab')$$, '23514', null, 'and doesn''t start with one');
select throws_ok($$select public.create_workspace('A', 'a_b')$$, '23514', null, 'and holds only letters, digits and hyphens');
select throws_ok($$select public.create_workspace('A', 'join')$$, '23514', null, 'and isn''t one of the app''s own');
select throws_ok($$select public.create_workspace('', 'blank')$$, '23514', null, 'A workspace has a name');

-- Ada invites a member.
select lives_ok(
  $$select set_config('test.link', public.create_invitation(current_setting('test.acme')::uuid, 'member'), true)$$,
  'An owner makes an invitation link'
);
select is(length(current_setting('test.link')), 64, 'whose token is long enough not to guess');
select throws_ok(
  $$select public.create_invitation(current_setting('test.acme')::uuid, 'admin')$$,
  '23514',
  null,
  'A link invites viewers and members, not admins'
);
select throws_ok(
  'select token_hash from public.invitations', '42501', null, 'No one reads a link''s hash'
);

-- Ben opens the link.
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);

select is_empty('select * from public.workspaces', 'Before joining, Ben sees no workspace');
select results_eq(
  $$select workspace_name, role from public.invitation(current_setting('test.link'))$$,
  $$values ('Acme', 'member'::public.workspace_role)$$,
  'The link says which workspace it is for, and as what'
);
select is(
  public.accept_invitation(current_setting('test.link')), 'acme', 'Joining gives the workspace''s address'
);
select results_eq(
  'select person_id, role from public.members order by role desc',
  $$values
    ('a0000000-0000-4000-8000-000000000001'::uuid, 'owner'::public.workspace_role),
    ('b0000000-0000-4000-8000-000000000002'::uuid, 'member'::public.workspace_role)$$,
  'Ben is a member, and sees who else is'
);
select results_eq(
  'select name from public.people order by name',
  $$values ('Ada Lovelace'), ('Ben')$$,
  'and their names, but no one else''s'
);
select is(
  public.accept_invitation(current_setting('test.link')), 'acme', 'Joining twice changes nothing'
);

-- What a member can't do.
select is_empty('select id from public.invitations', 'A member sees no invitations');
select throws_ok(
  $$select public.create_invitation(current_setting('test.acme')::uuid, 'member')$$,
  '42501', null, 'A member can''t invite people'
);
update public.workspaces set name = 'Renamed';
select results_eq('select name from public.workspaces', $$values ('Acme')$$, 'or rename the workspace');
select throws_ok(
  $$select public.set_member_role(current_setting('test.acme')::uuid, 'b0000000-0000-4000-8000-000000000002', 'admin')$$,
  '42501', null, 'or change a role, their own included'
);
select throws_ok(
  $$select public.remove_member(current_setting('test.acme')::uuid, 'a0000000-0000-4000-8000-000000000001')$$,
  '42501', null, 'or remove someone'
);
select throws_ok(
  $$select public.delete_workspace(current_setting('test.acme')::uuid)$$,
  '42501', null, 'or delete the workspace'
);
select throws_ok(
  $$insert into public.events (workspace_id, actor_kind, action, subject_type, subject_id)
    values (current_setting('test.acme')::uuid, 'person', 'x', 'x', 'x')$$,
  '42501', null, 'No one writes the history by hand'
);
select throws_ok('delete from public.events', '42501', null, 'or erases it');

-- Cy, in no workspace, sees nothing of Acme.
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);

select is_empty('select * from public.workspaces', 'An outsider sees no workspace');
select is_empty('select * from public.members', 'or its members');
select is_empty('select * from public.events', 'or its history');
select results_eq('select email from public.people', $$values ('cy@example.com')$$, 'and only themself');

-- Ada makes Ben an admin.
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);

select lives_ok(
  $$select public.set_member_role(current_setting('test.acme')::uuid, 'b0000000-0000-4000-8000-000000000002', 'admin')$$,
  'An owner makes a member an admin'
);
select results_eq(
  $$select action, changes from public.events where subject_id = 'b0000000-0000-4000-8000-000000000002' order by id desc limit 1$$,
  $$values ('member.updated', '{"role": ["member", "admin"]}'::jsonb)$$,
  'The change is logged with the role before and after'
);

-- What an admin can and can't do.
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);

update public.workspaces set name = 'Acme Labs';
select results_eq('select name from public.workspaces', $$values ('Acme Labs')$$, 'An admin renames the workspace');
select lives_ok(
  $$select set_config('test.viewers', public.create_invitation(current_setting('test.acme')::uuid, 'viewer'), true)$$,
  'and invites people'
);
select is(
  (select count(*)::integer from public.invitations), 2, 'and sees the workspace''s invitations'
);
select throws_ok(
  $$select public.set_member_role(current_setting('test.acme')::uuid, 'b0000000-0000-4000-8000-000000000002', 'owner')$$,
  '42501', null, 'An admin can''t make an owner'
);
select throws_ok(
  $$select public.remove_member(current_setting('test.acme')::uuid, 'a0000000-0000-4000-8000-000000000001')$$,
  '42501', null, 'or remove one'
);
delete from public.invitations where role = 'viewer';
select is(
  (select count(*)::integer from public.invitations), 1, 'An admin revokes a link'
);

-- Cy can't use a revoked or expired link.
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);

select is_empty(
  $$select * from public.invitation(current_setting('test.viewers'))$$, 'A revoked link offers nothing'
);
select throws_ok(
  $$select public.accept_invitation(current_setting('test.viewers'))$$,
  'P0002', null, 'and can''t be used'
);
reset role;
update public.invitations set expires_at = now() - interval '1 second';
set local role authenticated;
select throws_ok(
  $$select public.accept_invitation(current_setting('test.link'))$$,
  'P0002', null, 'and neither can an expired one'
);

-- A workspace keeps an owner.
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);

select throws_ok(
  $$select public.remove_member(current_setting('test.acme')::uuid, 'a0000000-0000-4000-8000-000000000001')$$,
  '23514', null, 'The only owner can''t leave'
);
select throws_ok(
  $$select public.set_member_role(current_setting('test.acme')::uuid, 'a0000000-0000-4000-8000-000000000001', 'admin')$$,
  '23514', null, 'or stop being an owner'
);
select throws_ok(
  'select public.close_account()', '23514', null, 'or close their account while others remain'
);
select lives_ok(
  $$select public.set_member_role(current_setting('test.acme')::uuid, 'b0000000-0000-4000-8000-000000000002', 'owner')$$,
  'An owner makes another owner'
);
select lives_ok(
  $$select public.remove_member(current_setting('test.acme')::uuid, 'a0000000-0000-4000-8000-000000000001')$$,
  'and then can leave'
);
select is_empty('select * from public.workspaces', 'and no longer sees the workspace');

-- Ben deletes the workspace, and everything in it goes with it.
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);

select lives_ok(
  $$select public.delete_workspace(current_setting('test.acme')::uuid)$$, 'An owner deletes the workspace'
);
reset role;
select is(
  (select count(*)::integer from public.members) + (select count(*)::integer from public.invitations)
    + (select count(*)::integer from public.events),
  0,
  'with its members, invitations and history'
);

-- Closing an account deletes the workspaces where the person was alone.
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);
select lives_ok($$select public.create_workspace('Solo', 'solo')$$, 'A person works alone');
select lives_ok(
  $$select set_config('test.solo', public.create_invitation((select id from public.workspaces where slug = 'solo'), 'member'), true)$$,
  'and invites someone'
);
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);
select lives_ok($$select public.accept_invitation(current_setting('test.solo'))$$, 'who joins');
select lives_ok('select public.close_account()', 'A member closes their account');
reset role;
select results_eq(
  $$select action, actor_kind::text, actor_id from public.events
    where workspace_id = (select id from public.workspaces where slug = 'solo') and action = 'member.deleted'$$,
  $$values ('member.deleted', 'person', null::uuid)$$,
  'and the workspace''s history says they left, without the closed account'
);
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);
select lives_ok('select public.close_account()', 'A person closes their account');
reset role;
select is(
  (select count(*)::integer from public.workspaces where slug = 'solo'), 0, 'and their own workspace goes too'
);

select * from finish();
rollback;
