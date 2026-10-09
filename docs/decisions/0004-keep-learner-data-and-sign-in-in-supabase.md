# 4. Keep learner data and sign-in in Supabase

- Status: accepted
- Date: 2026-10-08

## Context

Sulba needs a database for accounts, attempts, reviews and later discussions, and a sign-in service, at $0 while it grows. A Supabase project with sign-in configured already existed.

## Decision

Keep the existing Supabase project: Postgres with row-level security, Supabase sign-in, Realtime and Storage. Its old schema was removed on 8 October 2026, and a new one replaces it. GitHub holds code and course content only; every piece of learner data lives in Supabase.

## Options

| Option | Free storage | What stops an always-busy app at $0 | Sign-in | How the browser reaches the data |
| --- | --- | --- | --- | --- |
| Supabase (chosen) | 500 MB | Nothing while it's used: projects pause only after a week with no activity | Built in | Directly, each row guarded by row-level security |
| Neon with Neon Auth | 1 GB per project | Compute is capped at 100 CU-hours a project a month, about 400 hours at the smallest size, or roughly 13 hours a day. Then compute stops until the next month. | Managed Better Auth, 60,000 monthly users | Through Sulba's Worker |
| Cloudflare D1 with Better Auth | 5 GB | 5 million rows read and 100,000 written a day, then queries fail until midnight UTC | A library Sulba runs itself | Through the Worker only, with no row-level security |

## Evidence

[Supabase pricing](https://supabase.com/pricing), [Neon pricing](https://neon.com/pricing), [Neon's plans](https://neon.com/docs/introduction/plans), [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) and [Supabase Realtime's quotas](https://supabase.com/docs/guides/realtime/pricing) (200 concurrent connections and 2 million messages a month on the free plan).

## Why

It is the only option where sign-in, row-level security, realtime and storage come as one service at $0, and an app in daily use never reaches its pause. Neon's free compute stops a site that is busy around the clock partway through the month. D1 has more space, but no row-level security and no built-in sign-in, so every read would go through the Worker and count against its quota.

## Consequences

500 MB is the first limit Sulba meets. Old attempts are rolled up into per-session progress to put it off, and real usage will show when it arrives. Supabase Pro costs $25 a month and includes 8 GB of database, 250 GB of egress and 100,000 monthly users, with no pausing.

Migrations are plain Postgres SQL, and all data access goes through the `data` package. Only sign-in and the client are specific to Supabase, so a move to Neon or a self-run Postgres would rewrite one package.

## Revisit when

Supabase's prices or limits change enough that another option costs less at Sulba's size.
