-- A learner adds and reads only their own reviews, and can't change or remove one.
begin;
select plan(19);

insert into auth.users (id, email) values
  ('a0000000-0000-4000-8000-000000000001', 'a@example.com'),
  ('b0000000-0000-4000-8000-000000000002', 'b@example.com'),
  ('c0000000-0000-4000-8000-000000000003', 'c@example.com');

-- Without signing in, nothing.
set local role anon;

select throws_ok('select * from public.reviews', '42501', null, 'Visitors can''t read reviews');
select throws_ok(
  $$insert into public.reviews (id, learner_id, card_id, rating, reviewed_at)
    values ('10000000-0000-4000-8000-000000000000', 'a0000000-0000-4000-8000-000000000001',
      'crd_aaaaaa', 3, '2026-10-15 09:00+00')$$,
  '42501',
  null,
  'Visitors can''t add reviews'
);

-- Learner A reviews a card.
set local role authenticated;
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);

select lives_ok(
  $$insert into public.reviews (id, card_id, rating, reviewed_at)
    values ('10000000-0000-4000-8000-000000000001', 'crd_aaaaaa', 3, '2026-10-15 09:00+00')$$,
  'A learner adds a review'
);
select is(
  (select learner_id from public.reviews where id = '10000000-0000-4000-8000-000000000001'),
  'a0000000-0000-4000-8000-000000000001'::uuid,
  'A review belongs to the signed-in learner'
);
select lives_ok(
  $$insert into public.reviews (id, card_id, rating, reviewed_at)
    values ('10000000-0000-4000-8000-000000000001', 'crd_aaaaaa', 3, '2026-10-15 09:00+00')
    on conflict (id) do nothing$$,
  'A batch sent again is accepted'
);
select is((select count(*)::integer from public.reviews), 1, 'and adds nothing');

-- What a learner can't do.
select throws_ok(
  $$insert into public.reviews (id, learner_id, card_id, rating, reviewed_at)
    values ('10000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000002',
      'crd_aaaaaa', 3, '2026-10-15 09:00+00')$$,
  '42501',
  null,
  'A learner can''t add a review for someone else'
);
select throws_ok(
  $$insert into public.reviews (id, card_id, rating, reviewed_at, created_at)
    values ('10000000-0000-4000-8000-000000000003', 'crd_aaaaaa', 3, '2026-10-15 09:00+00', '2026-01-01')$$,
  '42501',
  null,
  'A learner can''t set when a review arrived'
);
select throws_ok('update public.reviews set rating = 4', '42501', null, 'A learner can''t change a review');
select throws_ok('delete from public.reviews', '42501', null, 'A learner can''t remove a review');

-- Reviews that make no sense are refused.
select throws_ok(
  $$insert into public.reviews (id, card_id, rating, reviewed_at)
    values ('10000000-0000-4000-8000-000000000004', 'stg_aaaaaa', 3, '2026-10-15 09:00+00')$$,
  '23514',
  null,
  'A card is named by its permanent id'
);
select throws_ok(
  $$insert into public.reviews (id, card_id, rating, reviewed_at)
    values ('10000000-0000-4000-8000-000000000005', 'crd_aaaaaa', 0, '2026-10-15 09:00+00')$$,
  '23514',
  null,
  'A rating is Again, Hard, Good or Easy'
);
select throws_ok(
  $$insert into public.reviews (id, card_id, rating, reviewed_at)
    values ('10000000-0000-4000-8000-000000000006', 'crd_aaaaaa', 5, '2026-10-15 09:00+00')$$,
  '23514',
  null,
  'and nothing past Easy'
);
select throws_ok(
  $$insert into public.reviews (id, card_id, rating, reviewed_at)
    values ('10000000-0000-4000-8000-000000000007', 'crd_aaaaaa', 3, now() + interval '2 days')$$,
  '23514',
  null,
  'A review can''t happen in the future'
);

-- Learner B sees none of it.
select set_config('request.jwt.claims', '{"sub": "b0000000-0000-4000-8000-000000000002", "role": "authenticated"}', true);

select is_empty('select * from public.reviews', 'Another learner can''t read the reviews');

-- Learner C reaches the daily limit.
select set_config('request.jwt.claims', '{"sub": "c0000000-0000-4000-8000-000000000003", "role": "authenticated"}', true);

select lives_ok(
  $$insert into public.reviews (id, card_id, rating, reviewed_at)
    select gen_random_uuid(), 'crd_aaaaaa', 3, now() from generate_series(1, 2000)$$,
  'A learner can add 2,000 reviews in a day'
);
select throws_ok(
  $$insert into public.reviews (id, card_id, rating, reviewed_at)
    values (gen_random_uuid(), 'crd_aaaaaa', 3, now())$$,
  'P0001',
  'More than 2,000 reviews in a day',
  'but no more'
);

-- Closing an account removes its reviews, and no one else's.
select set_config('request.jwt.claims', '{"sub": "a0000000-0000-4000-8000-000000000001", "role": "authenticated"}', true);
select lives_ok('select public.close_account()', 'A learner closes their account');

reset role;
select results_eq(
  'select distinct learner_id from public.reviews',
  $$values ('c0000000-0000-4000-8000-000000000003'::uuid)$$,
  'Closing an account removes its reviews, and no one else''s'
);

select * from finish();
rollback;
