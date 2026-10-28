# 48. Keep workspaces in shared tables guarded by row-level security, with a log of every change

- Status: accepted
- Date: 2026-10-27

## Context

The app (decision records 46 and 47) is used by teams. Each team works in a workspace, and each person in it has a role that decides what they may change. People sign in with GitHub or Google (decision record 19), so they join a workspace by an invitation rather than an account a team makes for them. Agents will act in a workspace too, on a person's behalf, and the team needs to see who or what changed each thing. The app reads Supabase from the browser, so Postgres must decide every read and write (decision record 4), and the hosted project is on Supabase's free plan, which allows two projects.

## Decision

- **Tables:** `people` (each account's name and email, copied from Supabase Auth by a trigger), `workspaces` (a name and an address, `sulba.dev/app/<slug>`, which can't change), `members` (a person's role in a workspace), `invitations` and `events`, in the one database every workspace shares. Every row of a workspace carries its `workspace_id`.
- **Roles:** viewer, member, admin and owner, each allowed what the one before is and more: a member makes changes, an admin invites people, changes their roles and renames the workspace, and an owner makes owners and deletes the workspace. A workspace always keeps an owner, and a person who is a workspace's only owner while others are in it can't close their account.
- **Row-level security:** every table has it, and every policy names `authenticated`. A policy compares the row's `workspace_id` with the set of the person's workspaces, `workspace_id in (select access.workspace_ids('admin'))`, from security definer functions in the `access` schema, which signed-in people may call and the Data API doesn't serve. Privileges are revoked first and granted column by column where a table holds what no one should read back, such as an invitation's token.
- **Changes people make:** reads go to the tables; changes go through functions in `public` (`create_workspace`, `create_invitation`, `accept_invitation`, `set_member_role`, `remove_member`, `delete_workspace`), which check the role, keep the rules above and raise a refusal written for the person who asked. Renaming a workspace and revoking an invitation are a policy on the table.
- **Invitations:** an admin makes a link that gives the viewer or member role and lasts 7 days, or until revoked. The link carries a token of 256 random bits; the database keeps only its SHA-256 hash, and shows the token once, to the admin who made it. A workspace has at most 50 open links, and a person owns at most 10 workspaces.
- **The log:** a trigger on each table writes every insert, update and delete to `events` in the same transaction: the workspace, the time, who acted (`person`, `agent`, `github` or `system`, with the person and, for an agent, its OAuth client from the token), an action such as `member.updated`, the subject and each field that changed as its value before and after. Fields that are secret, such as a token's hash, stay out of it. Members read their workspaces' events, and no one writes them but the trigger. Each event's id orders them, so the log is also where the app's live updates will start from.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Shared tables with a `workspace_id` on each row, guarded by row-level security (chosen) | One database and one set of migrations; Postgres refuses what a person may not do however the request is made; Supabase's guides show how to keep its policies fast | Every table and policy must carry the workspace and be tested, or a row leaks across workspaces |
| A schema for each workspace | Rows of different workspaces are apart by construction | Each new workspace needs DDL, every migration runs once per workspace, and the Data API serves only the schemas it's set up with |
| A Supabase project for each workspace | The strongest separation | The free plan has two projects |
| Roles as custom claims in the access token | A policy reads the role without a query | A claim is the token's snapshot: a removed member keeps access until their token is refreshed |
| Invitations by email, with Supabase Auth's `inviteUserByEmail` | The person gets an email | Its built-in email sends only to the project team's own addresses, 2 an hour, and it creates an email sign-in, while Sulba's people sign in with GitHub or Google |
| Invitations by email, sent by the Worker with Resend | Works with any sign-in, on Resend's free plan | Needs a server route and a secret before the first team can be invited; a link works without either and can go out by any channel |
| The log written by the app's code, as Plane does | Can describe a change in the product's words | Only as complete as the code paths that remember to write it |
| pgAudit | Records every statement | Writes to Postgres's log, which the free plan keeps for a day and the app can't show |

## Evidence

- [Supabase, Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security): grants and policies are separate checks, and adding a policy doesn't revoke a grant; naming the role on each policy, indexing the columns policies filter on, and wrapping functions in `select` so they run once a statement; a security definer function in an exposed schema can be called over the Data API with its owner's privileges.
- [Supabase, RLS performance and best practices](https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv): comparing the row's column with a set of ids, `team_id in (select …)`, rather than the person with each row's members (9,000 ms to 20 ms in its measurement), and security definer helpers to avoid the members table's own policy and the infinite recursion of two policies that read each other.
- [Supabase, Custom Claims and RBAC](https://supabase.com/docs/guides/database/postgres/custom-claims-and-role-based-access-control-rbac) and [Custom Access Token Hook](https://supabase.com/docs/guides/auth/auth-hooks/custom-access-token-hook): roles carried as claims, and the claims a token holds until it is refreshed.
- [Supabase, Custom SMTP](https://supabase.com/docs/guides/auth/auth-smtp) and [`auth.admin.inviteUserByEmail`](https://supabase.com/docs/reference/javascript/auth-admin-inviteuserbyemail): the built-in email service sends only to the project team's addresses, at 2 emails an hour, and isn't meant for production; the invite call is an admin call that doesn't support PKCE.
- [Supabase, pricing](https://supabase.com/pricing): two active projects on the free plan, and logs kept for one day.
- [Resend, pricing](https://resend.com/pricing): 3,000 emails a month and 100 a day on the free plan.
- [PostgreSQL, Trigger functions](https://www.postgresql.org/docs/current/plpgsql-trigger.html): Example 41.4, a row trigger that writes each change to an audit table.
- [Oliver Rice, Postgres Auditing in 150 lines of SQL](https://supabase.com/blog/postgres-audit) (March 8, 2022): one table of changes written by a generic trigger, whose overhead is negligible below about 1,000 writes a second.
- [Supabase, PGAudit](https://supabase.com/docs/guides/database/extensions/pgaudit): it records to Postgres's standard log.
- [Linear, Audit log](https://linear.app/docs/audit-log) and [Agents in Linear](https://linear.app/docs/agents-in-linear): an agent's actions show in the same activity as a teammate's.
- Measured on this repository: `packages/data/supabase/tests/workspaces.test.sql` runs 68 pgTAP tests of these rules in a local Supabase, among them that an outsider reads none of a workspace's rows, that a role change is logged as `{"role": ["member", "admin"]}`, that an expired or revoked link joins no one, and that a member who closes their account leaves the history without their id.

## Why

Shared tables under row-level security are what Supabase's guides are written for, and they put every rule in Postgres, which is the only place the browser can't get around. A role read from the members table takes effect on the next request, which matters when someone is removed. The rules that span rows, such as keeping an owner, live in functions that raise sentences a person can act on, so the app shows Postgres's refusal rather than repeating its rules. A link invites anyone a team can message, needs no server or secret, and can be revoked; email invitations can arrive later without changing it. A trigger-written log can't be skipped by any way of writing, and the same log serves the activity a team reads and the live updates the app will need.

The strongest case against it is isolation: one missing `workspace_id` filter in a policy exposes a workspace to every signed-in person. The pgTAP tests check each table's policies as an outsider, and every new table joins them.

## Consequences

- Every table a workspace's work goes into carries `workspace_id`, a policy on it and a trigger that writes its changes to `events`, with pgTAP tests in the same pull request.
- The log grows with every change; it has two btree indexes and no expiry until a team needs one.
- An invitation link can be passed on: anyone who has it can join until it expires or is revoked, which the invite dialog says.

## Revisit when

A customer needs its data in a database of its own, a workspace's events outgrow one table, or invitations need to reach people by email.
