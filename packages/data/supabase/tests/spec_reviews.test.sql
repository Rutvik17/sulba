-- A spec's members name its reviewers from the workspace's people, a spec with reviewers is
-- approved when the last of them approves, and a change while it's in review asks its approvers
-- again, while a request for changes stands until its reviewer answers again.
begin;
select plan(35);

insert into auth.users (id, email, raw_user_meta_data) values
  ('a0000000-0000-4000-8000-000000000001', 'ada@example.com', '{"full_name": "Ada Lovelace"}'),
  ('b0000000-0000-4000-8000-000000000002', 'ben@example.com', '{"name": "Ben"}'),
  ('c0000000-0000-4000-8000-000000000003', 'cy@example.com', '{}'),
  ('d0000000-0000-4000-8000-000000000004', 'dee@example.com', '{}');

create function pg_temp.as_person(person text) returns void language sql as $$
  select set_config('request.jwt.claims', json_build_object('sub', person, 'role', 'authenticated')::text, true)
$$;
create function pg_temp.verdicts() returns text language sql as $$
  select string_agg(p.email || ' ' || r.verdict, ', ' order by p.email)
  from public.spec_reviews r join public.people p on p.id = r.reviewer_id
  where r.spec_id = current_setting('test.spec')::uuid
$$;

select ok(
  not has_function_privilege('anon', 'public.review_spec(uuid, public.review_verdict, text)', 'execute'),
  'Visitors can''t review'
);
select ok(
  not has_table_privilege('authenticated', 'public.spec_reviews', 'insert')
    and not has_table_privilege('authenticated', 'public.spec_reviews', 'update'),
  'and reviews change only through their functions'
);

-- Ada's workspace, with Ben as a member and Cy as a viewer; Ada writes a spec.
set local role authenticated;
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select set_config('test.acme', (select id::text from public.create_workspace('Acme', 'acme')), true);
select set_config('test.member', public.create_invitation(current_setting('test.acme')::uuid, 'member'), true);
select set_config('test.viewer', public.create_invitation(current_setting('test.acme')::uuid, 'viewer'), true);
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select public.accept_invitation(current_setting('test.member'));
select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select public.accept_invitation(current_setting('test.viewer'));
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select public.create_spec(current_setting('test.acme')::uuid, 'Retry failed payments', array['Retries once after 30 seconds']);
select set_config('test.spec', (select id::text from public.specs where number = 1), true);
select set_config('test.criterion', (select id::text from public.criteria where number = 1), true);

-- Ada asks Ben and Cy to review it.
select lives_ok(
  $$select public.request_review(current_setting('test.spec')::uuid, 'b0000000-0000-4000-8000-000000000002')$$,
  'A member asks a member to review a spec'
);
select lives_ok(
  $$select public.request_review(current_setting('test.spec')::uuid, 'c0000000-0000-4000-8000-000000000003')$$,
  'and a viewer'
);
select throws_ok(
  $$select public.request_review(current_setting('test.spec')::uuid, 'a0000000-0000-4000-8000-000000000001')$$,
  '23514', 'A spec''s owner doesn''t review it', 'The owner doesn''t review their own spec'
);
select throws_ok(
  $$select public.request_review(current_setting('test.spec')::uuid, 'd0000000-0000-4000-8000-000000000004')$$,
  '23514', 'A reviewer is one of the workspace''s people', 'nor does someone outside the workspace'
);
select results_eq(
  $$select action, actor_id from public.events where subject_type = 'review' order by id$$,
  $$values ('review.created', 'a0000000-0000-4000-8000-000000000001'::uuid), ('review.created', 'a0000000-0000-4000-8000-000000000001'::uuid)$$,
  'The history says who asked for each review'
);

select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select throws_ok(
  $$select public.request_review(current_setting('test.spec')::uuid, 'b0000000-0000-4000-8000-000000000002')$$,
  '42501', 'Only members can choose a spec''s reviewers', 'A viewer doesn''t choose reviewers'
);
select is((select count(*) from public.spec_reviews), 2::bigint, 'but sees the spec''s reviews');
select throws_ok(
  $$select public.review_spec(current_setting('test.spec')::uuid, 'approved')$$,
  '23514', 'Only a spec in review can be reviewed', 'A draft isn''t reviewed yet'
);

-- In review, Ben approves, and it waits for Cy.
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select throws_ok(
  $$update public.specs set status = 'approved' where id = current_setting('test.spec')::uuid$$,
  '23514', 'Every reviewer has to approve the spec first', 'A spec with reviewers isn''t approved by hand'
);
update public.specs set status = 'in_review' where id = current_setting('test.spec')::uuid;
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select is(
  public.review_spec(current_setting('test.spec')::uuid, 'approved', 'Looks right'),
  'in_review'::public.spec_status,
  'One approval leaves it in review'
);
select is(pg_temp.verdicts(), 'ben@example.com approved, cy@example.com pending', 'until every reviewer approves');

-- Ada edits its text, and Ben is asked again.
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
update public.specs set body = 'Cards fail.' where id = current_setting('test.spec')::uuid;
select is(pg_temp.verdicts(), 'ben@example.com pending, cy@example.com pending', 'Editing it asks its approvers again');
select is(
  (select note from public.spec_reviews where reviewer_id = 'b0000000-0000-4000-8000-000000000002'),
  null,
  'without the note of an answer to another version'
);

-- Ben approves again; Cy asks for changes, and must say what.
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select public.review_spec(current_setting('test.spec')::uuid, 'approved');
select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select throws_ok(
  $$select public.review_spec(current_setting('test.spec')::uuid, 'changes_requested', '  ')$$,
  '23514', 'Say what to change', 'Asking for changes says what to change'
);
select throws_ok(
  $$select public.review_spec(current_setting('test.spec')::uuid, 'pending')$$,
  '22023', null, 'A review answers'
);
select is(
  public.review_spec(current_setting('test.spec')::uuid, 'changes_requested', 'Say how long it waits'),
  'in_review'::public.spec_status,
  'A viewer asks for changes'
);

-- Ada rewords its criterion: Ben is asked again, and Cy's request stands.
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
update public.criteria set text = 'Retries once, 30 seconds after it fails' where id = current_setting('test.criterion')::uuid;
select is(
  pg_temp.verdicts(),
  'ben@example.com pending, cy@example.com changes_requested',
  'Rewording a criterion asks its approvers again, and a request for changes stands'
);
select is(
  (select note from public.spec_reviews where reviewer_id = 'c0000000-0000-4000-8000-000000000003'),
  'Say how long it waits',
  'with what it asked'
);
select public.add_criterion(current_setting('test.spec')::uuid, 'Keeps the idempotency key');
select pg_temp.as_person('b0000000-0000-4000-8000-000000000002');
select public.review_spec(current_setting('test.spec')::uuid, 'approved');
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select throws_ok(
  $$select public.review_spec(current_setting('test.spec')::uuid, 'approved')$$,
  '42501', 'Only the spec''s reviewers can review it', 'Someone not asked doesn''t review'
);
select lives_ok(
  $$select public.request_review(current_setting('test.spec')::uuid, 'c0000000-0000-4000-8000-000000000003')$$,
  'The owner asks Cy again'
);
select is(pg_temp.verdicts(), 'ben@example.com approved, cy@example.com pending', 'which leaves Ben''s approval');

-- Cy approves, which approves the spec.
select pg_temp.as_person('c0000000-0000-4000-8000-000000000003');
select is(
  public.review_spec(current_setting('test.spec')::uuid, 'approved'),
  'approved'::public.spec_status,
  'The last approval approves the spec'
);
select is(
  (select status from public.specs where id = current_setting('test.spec')::uuid),
  'approved'::public.spec_status,
  'as its status says'
);
select results_eq(
  $$select actor_id from public.events where action = 'spec.updated' and changes ? 'status' order by id desc limit 1$$,
  $$values ('c0000000-0000-4000-8000-000000000003'::uuid)$$,
  'and the history says whose approval it was'
);
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
select throws_ok(
  $$select public.request_review(current_setting('test.spec')::uuid, 'b0000000-0000-4000-8000-000000000002')$$,
  '23514', 'Only a draft or a spec in review takes reviewers', 'An approved spec takes no more reviewers'
);

-- Back in review, a new round begins.
update public.specs set status = 'draft' where id = current_setting('test.spec')::uuid;
update public.specs set status = 'in_review' where id = current_setting('test.spec')::uuid;
select is(pg_temp.verdicts(), 'ben@example.com pending, cy@example.com pending', 'Going into review again asks every reviewer again');

-- An agent doesn't review or choose reviewers.
select set_config('request.jwt.claims', json_build_object(
  'sub', 'b0000000-0000-4000-8000-000000000002', 'role', 'authenticated',
  'client_id', 'e0000000-0000-4000-8000-000000000005'
)::text, true);
select throws_ok(
  $$select public.review_spec(current_setting('test.spec')::uuid, 'approved')$$,
  '42501', 'An agent can''t review a spec. A person does that in Sulba', 'An agent doesn''t review'
);
select throws_ok(
  $$select public.remove_reviewer(current_setting('test.spec')::uuid, 'c0000000-0000-4000-8000-000000000003')$$,
  '42501', null, 'or choose reviewers'
);

-- Someone outside the workspace sees none of it.
select pg_temp.as_person('d0000000-0000-4000-8000-000000000004');
select is_empty($$select from public.spec_reviews$$, 'Someone outside the workspace sees no reviews');
select throws_ok(
  $$select public.request_review(current_setting('test.spec')::uuid, 'd0000000-0000-4000-8000-000000000004')$$,
  '42501', null, 'or asks for one'
);

-- Ben comes to own the spec, so stops reviewing it; Cy leaves, so stops too.
select pg_temp.as_person('a0000000-0000-4000-8000-000000000001');
update public.specs set owner_id = 'b0000000-0000-4000-8000-000000000002' where id = current_setting('test.spec')::uuid;
select is(pg_temp.verdicts(), 'cy@example.com pending', 'A reviewer who comes to own the spec stops reviewing it');
select public.remove_member(current_setting('test.acme')::uuid, 'c0000000-0000-4000-8000-000000000003');
select is(pg_temp.verdicts(), null, 'and one who leaves the workspace stops too');
select lives_ok(
  $$update public.specs set status = 'approved' where id = current_setting('test.spec')::uuid$$,
  'A spec with no reviewers is approved by a member'
);


select * from finish();
rollback;
