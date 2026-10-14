-- Closing an account deletes the signed-in learner from auth.users, and with them everything that
-- references it: their sessions, their sign-in identities, and every attempt, stage's progress and
-- study day. The Data API serves it as an RPC to signed-in learners only, and it can reach no row
-- but the caller's own.
create function public.close_account()
returns void
language sql
security definer
set search_path = ''
as $$
  delete from auth.users where id = (select auth.uid());
$$;

revoke execute on function public.close_account() from public, anon;
grant execute on function public.close_account() to authenticated;
