# 18. Keep progress as a log of attempts

- Status: accepted
- Date: 2026-10-14

## Context

Accounts arrive in Phase 3, and a learner's progress has to follow them from device to device. The workspace already keeps each stage's code, the stages passed and each finished Catch review in the browser, and it works offline, so changes reach Supabase late, in batches, sometimes twice, and from more than one device. The browser reaches Supabase directly, each row guarded by row-level security ([record 4](0004-keep-learner-data-and-sign-in-in-supabase.md)). The free plan holds 500 MB. The course plan's hours are estimates, to be recalibrated from the time learners spend. A learner's code stays on their device.

## Decision

- **The log:** the browser adds attempts to an append-only table: each run of the tests, hint opened, solution viewed and pass, with the stage's id and version, how many tests and checks passed, a finished Catch review, the time spent and the day it was where the learner is. The browser makes each attempt's id, so a batch sent twice adds nothing.
- **Progress:** a trigger folds each attempt into its stage's progress and the learner's study day, in ways the order of arrival can't change: counts and time add up, the most hints opened wins, and the earliest pass wins with its review.
- **Access:** a signed-in learner adds and reads only their own attempts, and reads only their own progress and study days. Nothing can be changed or removed, except by closing the account, which removes it all. Visitors who aren't signed in reach nothing, and the trigger's functions sit in a schema the Data API doesn't serve.
- **Limits:** an account can add 2,000 attempts a day, so no single account can fill the database. Code is never stored.
- **Tests:** the migrations live in `packages/data`, and pgTAP tests in CI prove each rule above in a local Supabase.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A log of attempts, with progress kept by a trigger (chosen) | Retries, offline batches and two devices merge without losing anything; time is kept per stage and per day; old attempts can be rolled up later without touching progress | More SQL than writing rows directly; attempts take space until they're rolled up |
| The browser writes each stage's progress row | One row per stage and one upsert | An upsert merges by default, so the device that syncs last wins and a stale one can undo a pass; no record of time or runs |
| A log of attempts, with progress as a view over it | No trigger, and progress can't drift from the log | Every read aggregates the learner's whole log, and no attempt can ever be removed without changing progress |
| A sync engine: PowerSync, Electric or Zero | A local database kept in step with Postgres | Another service with its own limits: PowerSync's free plan allows 50 concurrent clients and pauses after a week idle, Electric bills writes, and Zero's hosted plans start at $30 a month |
| Writes through the Worker's API | The server can check anything before it's saved | Each write spends one of the Worker's 100,000 free requests a day on checks that row-level security already makes |

## Evidence

- Wrapping `auth.uid()` in a select lets Postgres "cache" the result "per-statement, rather than calling the function on each row"; every policy should name its role with `to`; the columns policies filter on should be indexed; and "Adding policies doesn't take those grants back", so grants are revoked and given back role by role ([Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)).
- From 30 October 2026, Supabase stops granting new tables in existing projects to the Data API's roles ([changelog](https://supabase.com/changelog/45329-breaking-change-tables-not-exposed-to-data-and-graphql-api-automatically)). The migration grants and revokes explicitly, so it works the same on either side of that date.
- A `security definer` function must set its `search_path` ([Database functions](https://supabase.com/docs/guides/database/functions)), and shouldn't live in a schema the Data API serves ([Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)).
- `supabase test db` runs the pgTAP files in `supabase/tests`, each in its own transaction that is rolled back afterwards ([CLI reference](https://supabase.com/docs/reference/cli/supabase-test-db)).
- supabase-js's `upsert` merges duplicates unless `ignoreDuplicates` is set, which sends `Prefer: resolution=ignore-duplicates` ([postgrest-js](https://github.com/supabase/supabase-js/blob/master/packages/core/postgrest-js/src/PostgrestQueryBuilder.ts)). Such an insert also checks the table's select policies ([CREATE POLICY](https://www.postgresql.org/docs/17/sql-createpolicy.html)), so learners can read their own attempts.
- PowerSync's free plan allows 2 GB synced a month, 500 MB hosted and 50 peak concurrent clients, and free projects are deactivated after a week of inactivity ([PowerSync pricing](https://www.powersync.com/pricing)). Electric charges $1 per million writes, and $3 for live Postgres changes ([Electric pricing](https://electric.ax/pricing)). Zero is self-hostable, and its hosted plans start at $30 a month ([Zero](https://zero.rocicorp.dev/)).
- In a local Supabase, an attempt takes about 190 bytes with its indexes, so 500 MB holds about 2.6 million attempts.

## Why

Attempts can only be added, and every way they change progress gives the same result in any order, so a retried batch, a week offline or two devices can't lose a pass or count one twice. The log also records time spent on each stage, which the course plan's hours need. Postgres does the work in the same request that stores the attempt, at no cost to the Worker, and row-level security with explicit grants keeps each learner to their own rows. The strongest case against: the trigger is logic in the database, where it's less visible than code in the app, and the pgTAP tests are its only guard.

## Consequences

The browser needs a queue of unsent attempts that survives a reload and waits when the network or the daily limit refuses it, and it reads progress once a visit; that comes with sync. Results remain practice: a learner can send any attempt they like. Old attempts have to be rolled up into progress before the database nears 500 MB. Profiles arrive with sign-in, and review cards with spaced review.

## Revisit when

The database nears 500 MB, learners need to correct or erase a single attempt, or a sync engine's free tier covers what Sulba needs.
