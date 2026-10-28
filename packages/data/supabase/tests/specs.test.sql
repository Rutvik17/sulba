-- A workspace's specs reach its members alone, members and above write them, each spec and
-- criterion keeps a number no other is given, and the history says what changed without
-- keeping a spec's whole text each time it's saved.
begin;
select plan(37);

insert into auth.users (id, email, raw_user_meta_data) values
  ('a0000000-0000-4000-8000-000000000001', 'ada@example.com', '{"full_name": "Ada Lovelace"}'),
  ('b0000000-0000-4000-8000-000000000002', 'ben@example.com', '{"name": "Ben"}'),
  ('c0000000-0000-4000-8000-000000000003', 'cy@example.com', '{}');

select schema_privs_are('private', 'authenticated', array[]::text[], 'Signed-in people can''t reach the numbers');
select ok(
  not has_function_privilege('anon', 'public.create_spec(uuid, text, text[])', 'execute'),
  'Visitors can''t call create_spec'
);
select ok(
  not has_function_privilege('anon', 'public.add_criterion(uuid, text)', 'execute'),
  'or add_criterion'
);

-- Ada's workspace, with Ben as a viewer.
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);
select set_config('test.acme', (select id::text from public.create_workspace('Acme', 'acme')), true);
select set_config('test.link', public.create_invitation(current_setting('test.acme')::uuid, 'viewer'), true);
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);
select public.accept_invitation(current_setting('test.link'));

-- Without signing in, nothing.
reset role;
set local role anon;
select throws_ok('select id from public.specs', '42501', null, 'Visitors can''t read specs');
select throws_ok('select id from public.criteria', '42501', null, 'or criteria');
select throws_ok(
  $$select public.create_spec(current_setting('test.acme')::uuid, 'Retry failed payments')$$,
  '42501', null, 'or write one'
);

-- Ada writes specs.
reset role;
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);

select is(
  public.create_spec(
    current_setting('test.acme')::uuid,
    ' Retry failed payments ',
    array['When a payment fails, the system shall retry it once after 30 seconds', ' ', 'The retry uses the same idempotency key']
  ),
  1,
  'A member writes a spec, numbered 1'
);
select set_config('test.spec', (select id::text from public.specs where number = 1), true);
select results_eq(
  'select title, status::text, owner_id, created_by from public.specs',
  $$values ('Retry failed payments', 'draft', 'a0000000-0000-4000-8000-000000000001'::uuid, 'a0000000-0000-4000-8000-000000000001'::uuid)$$,
  'as a draft its writer owns'
);
select results_eq(
  'select number, text from public.criteria order by number',
  $$values (1, 'When a payment fails, the system shall retry it once after 30 seconds'), (2, 'The retry uses the same idempotency key')$$,
  'with its criteria numbered in order, blank ones left out'
);
select is(
  public.create_spec(current_setting('test.acme')::uuid, 'Export invoices'), 2, 'The next spec is 2'
);
select throws_ok(
  $$select public.create_spec(current_setting('test.acme')::uuid, '')$$, '23514', null, 'A spec has a title'
);
select throws_ok(
  $$select public.create_spec(current_setting('test.acme')::uuid, 'Too many', array_fill('A criterion'::text, array[101]))$$,
  '54000', null, 'and at most 100 criteria'
);

-- Criteria keep their numbers.
select is(public.add_criterion(current_setting('test.spec')::uuid, 'Retries are logged'), 3, 'A criterion is added as 3');
select lives_ok(
  $$delete from public.criteria where spec_id = current_setting('test.spec')::uuid and number = 3$$,
  'and removed'
);
select is(
  public.add_criterion(current_setting('test.spec')::uuid, 'Retries show on the invoice'), 4,
  'and the next is 4, never 3 again'
);
select lives_ok(
  $$update public.criteria set text = 'When a payment fails, the system shall retry it once after 60 seconds' where spec_id = current_setting('test.spec')::uuid and number = 1$$,
  'A member rewords a criterion'
);
select throws_ok(
  $$update public.criteria set number = 9 where spec_id = current_setting('test.spec')::uuid$$,
  '42501', null, 'but not its number'
);
select throws_ok(
  $$update public.specs set number = 9 where id = current_setting('test.spec')::uuid$$,
  '42501', null, 'or a spec''s'
);
select throws_ok(
  $$delete from public.specs where id = current_setting('test.spec')::uuid$$,
  '42501', null, 'A spec isn''t deleted'
);

-- Changing a spec, and what the history keeps of it.
select lives_ok(
  $$update public.specs set status = 'in_review', title = 'Retry a failed payment' where id = current_setting('test.spec')::uuid$$,
  'A member moves a spec to review and renames it'
);
select results_eq(
  $$select changes from public.events where subject_id = current_setting('test.spec') order by id desc limit 1$$,
  $$values ('{"status": ["draft", "in_review"], "title": ["Retry failed payments", "Retry a failed payment"]}'::jsonb)$$,
  'and the history keeps both changes'
);
select lives_ok(
  $$update public.specs set body = '## Context' || chr(10) || 'Cards fail at random.' where id = current_setting('test.spec')::uuid$$,
  'Writing its text'
);
select lives_ok(
  $$update public.specs set body = body || ' Most succeed a minute later.' where id = current_setting('test.spec')::uuid$$,
  'and writing more'
);
select results_eq(
  $$select action, changes from public.events
    where subject_id = current_setting('test.spec') and action = 'spec.updated' and changes ? 'body'$$,
  $$values ('spec.updated', '{"body": null}'::jsonb)$$,
  'is one change in the history, without the text'
);
select lives_ok(
  $$update public.specs set title = title where id = current_setting('test.spec')::uuid$$, 'Saving no change'
);
select is(
  (select count(*)::integer from public.events where subject_id = current_setting('test.spec')),
  3,
  'leaves the history as it was'
);
select results_eq(
  $$select action, spec_id::text from public.events where subject_type = 'criterion' order by id$$,
  $$values ('criterion.created', current_setting('test.spec')), ('criterion.created', current_setting('test.spec')),
           ('criterion.created', current_setting('test.spec')), ('criterion.deleted', current_setting('test.spec')),
           ('criterion.created', current_setting('test.spec')), ('criterion.updated', current_setting('test.spec'))$$,
  'Each criterion''s changes belong to its spec'
);

-- Owners.
select throws_ok(
  $$update public.specs set owner_id = 'c0000000-0000-4000-8000-000000000003' where id = current_setting('test.spec')::uuid$$,
  '23514', null, 'A spec''s owner is one of the workspace''s members'
);
select lives_ok(
  $$update public.specs set owner_id = 'b0000000-0000-4000-8000-000000000002' where id = current_setting('test.spec')::uuid$$,
  'Any member can own it'
);
select lives_ok(
  $$select public.remove_member(current_setting('test.acme')::uuid, 'b0000000-0000-4000-8000-000000000002')$$,
  'and when they leave'
);
select is(
  (select owner_id from public.specs where id = current_setting('test.spec')::uuid), null, 'they no longer own it'
);

-- A viewer reads specs and changes none.
select set_config('test.link', public.create_invitation(current_setting('test.acme')::uuid, 'viewer'), true);
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);
select public.accept_invitation(current_setting('test.link'));
select is((select count(*)::integer from public.specs), 2, 'A viewer reads the specs');
select throws_ok(
  $$select public.add_criterion(current_setting('test.spec')::uuid, 'Viewers can''t add this')$$,
  '42501', null, 'but adds no criterion'
);
select is_empty(
  $$update public.specs set title = 'Changed' where id = current_setting('test.spec')::uuid returning id$$,
  'and changes no spec'
);
select is_empty(
  $$delete from public.criteria where spec_id = current_setting('test.spec')::uuid returning id$$,
  'or criterion'
);

-- Someone outside the workspace sees none of it.
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);
select is_empty('select id from public.specs', 'Someone who left sees no spec');
select is_empty('select id from public.criteria', 'and no criterion');

select * from finish();
rollback;
