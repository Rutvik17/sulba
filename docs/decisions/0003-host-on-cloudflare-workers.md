# 3. Host on Cloudflare Workers

- Status: accepted
- Date: 2026-10-08

## Context

Sulba needs hosting that costs nothing until paying learners cover it, allows a commercial product, and runs Astro with server routes.

## Decision

One Cloudflare Worker, `sulba`, serves the built pages as static files and renders the rest. GitHub Actions deploys it with Wrangler after the checks pass: `main` goes to production, and every other branch gets its own preview address.

## Options

| Option | Free tier | Commercial use on the free tier | Notes |
| --- | --- | --- | --- |
| Cloudflare Workers (chosen) | Static files free and unlimited; 100,000 server requests a day at 10 ms of CPU each | Allowed | Runs Astro natively. The paid plan is $5 a month with 10 million requests included. |
| Vercel Hobby | 100 GB of transfer, 1 million function calls and 4 hours of CPU a month | "Hobby teams are restricted to non-commercial personal use only" | The best home for Next.js, but Sulba would need Pro once it earns anything |
| A free virtual machine (Oracle) | 2 CPU cores and 12 GB of memory since June 2026 | Allowed | One region, and Sulba would patch, secure and monitor the server itself |

## Evidence

[Cloudflare Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/), [Vercel's fair use guidelines](https://vercel.com/docs/limits/fair-use-guidelines) and [Oracle's Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm).

## Why

It is the only option that is free, allows a commercial product, runs in every region without servers to patch, and is Astro's own platform. Static files never count against the request quota, and they are most of Sulba's traffic.

## Consequences

Each server request gets 10 ms of CPU on the free plan, so server routes must stay light. Route caching and per-route CPU logs keep that in check, and the paid plan raises the limit.

## Revisit when

A workload needs long-running processes or GPUs, such as server grading or a GPU queue. Those go to a sandbox service, not the Worker.
