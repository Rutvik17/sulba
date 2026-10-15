-- Spaced review, kept as a log of each answer to a review card. The browser adds reviews, and
-- works out each card's schedule from them (decision record 20). Every row belongs to one
-- signed-in learner, and only they can read it. Closing an account removes their reviews with it.

create table public.reviews (
  -- Made by the browser, so a batch sent twice adds nothing the second time.
  id uuid primary key,
  learner_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  card_id text not null check (card_id ~ '^crd_[0-9a-z]{6}$'),
  -- Again, Hard, Good or Easy.
  rating smallint not null check (rating between 1 and 4),
  -- When the learner answered, by their clock.
  reviewed_at timestamptz not null,
  -- When it arrived, by the database's clock.
  created_at timestamptz not null default now(),
  constraint reviewed_before_arrival check (reviewed_at < created_at + interval '1 day')
);

-- Serves the row-level security policies, the daily limit below and reading a learner's log.
create index reviews_by_learner on public.reviews (learner_id, created_at);

-- As with attempts, one account can't fill the database: past 2,000 reviews in a day, more are
-- refused.
create function private.limit_reviews()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if (
    select count(*) from public.reviews
    where learner_id = new.learner_id and created_at > now() - interval '1 day'
  ) >= 2000 then
    raise exception 'More than 2,000 reviews in a day';
  end if;
  return new;
end;
$$;

create trigger limit_reviews
before insert on public.reviews
for each row execute function private.limit_reviews();

revoke execute on function private.limit_reviews() from public;

-- Only signed-in learners reach the table, and only their own rows. A review can't be changed or
-- removed once sent, and the arrival time is the database's, so the daily limit can't be dodged.
alter table public.reviews enable row level security;

revoke all on public.reviews from anon, authenticated;
grant select on public.reviews to authenticated;
grant insert (id, learner_id, card_id, rating, reviewed_at) on public.reviews to authenticated;

create policy "Learners add their own reviews" on public.reviews
for insert to authenticated with check (learner_id = (select auth.uid()));

create policy "Learners read their own reviews" on public.reviews
for select to authenticated using (learner_id = (select auth.uid()));
