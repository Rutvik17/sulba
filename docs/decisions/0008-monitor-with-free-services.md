# 8. Monitor with free services, each with one job

- Status: accepted
- Date: 2026-10-08

## Context

Sulba needs server logs, error reports and visit counts at $0, without tracking learners.

## Decision

| Need | Service | Free tier |
| --- | --- | --- |
| Server logs, including CPU time per route | Cloudflare Workers Logs | 200,000 log events a day, kept for 3 days |
| Errors in the browser and on the server | Sentry, Developer plan | One user, 5,000 errors and 5 million trace spans |
| Visits and page speed | Cloudflare Web Analytics | Free, and it "does not collect or use your visitors' personal data" |

Learning analytics (runs, passes, hints and time) come from Sulba's own `attempts` table, not from a tracker.

## Evidence

[Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/), [Sentry pricing](https://sentry.io/pricing/) and [Cloudflare Web Analytics](https://developers.cloudflare.com/web-analytics/about/).

## Why

Each service covers what the others can't see, and all three are free at Sulba's size.

## Consequences

The free plan keeps logs for only 3 days, so anything worth keeping becomes a Sentry event or a database row.

## Revisit when

Sulba outgrows one of these free tiers.
