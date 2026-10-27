# 47. Build the app in React, drawn in the browser and served by the site's Worker under /app/

- Status: accepted
- Date: 2026-10-27

## Context

The product (decision record 46) is an app behind sign-in: editors for specs and architecture, a board of tasks, updates as agents report back, and a map of links, with many screens that share the same workspace and selection. No search engine needs to see it. The Academy is Astro, its pages built ahead of time (decision records 1 and 2), on the Cloudflare Worker `web` (decision record 3), and the product's hosting costs nothing until customers pay. On Workers Free, a request gets 10 ms of CPU time, and the account 100,000 requests a day, while requests for static assets are free and unlimited.

## Decision

- **The app:** `apps/app`, a React 19 app built with Vite 8 and routed in the browser by TanStack Router, in TypeScript at the repository's strictest settings, with `packages/ui`'s tokens and components. It reaches Supabase from the browser through `packages/data`, where row-level security decides what it can read (decision record 4), and loads supabase-js only once the browser holds a session.
- **Where:** the site's Worker serves it at `/app/`. Each build of the site builds the app with Vite into the site's files (`apps/web/app.ts`), and `public/_redirects` answers every address under `/app/` but its files with its page, so a link to any of its pages works and the Worker runs no code for it.
- **Sign-in:** the app shares the site's origin, so it shares its session: a person signs in on the site's sign-in page, which sends them back to the app, and signing out of either signs out of both.
- **Server work:** what the app needs a server for, such as GitHub's webhooks, the MCP server agents connect to and calls to a model, runs as routes on the same Worker when a feature needs it. Such a request mostly waits on the network, which doesn't count as CPU time.
- **Development:** `pnpm dev:app` serves the app with Vite at http://127.0.0.1:4323/app/ and passes every other address to the site's dev server, `pnpm dev`, so the two share an origin there too.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A React app built with Vite and TanStack Router, drawn in the browser and served from the site's Worker (chosen) | Its pages are static files, which are free and spend no CPU; it reuses the site's React components and editor; every part is mature | Its page is blank until its script runs, and routing, data loading and server routes are put together here rather than given by a framework |
| Next.js with vinext on Workers | The largest ecosystem, with server components and actions | Rendering on the server spends CPU on every request against Workers Free's 10 ms, and vinext 1.0 is weeks old |
| Next.js on Vercel | Next.js's own platform | Vercel's Hobby plan is for non-commercial personal use only, so a product needs Pro |
| React Router or TanStack Start, rendering on the Worker | Full-stack React with first-class Workers support | The same CPU for server rendering, spent on pages no search engine sees |
| Astro with React islands, as the Academy | Already in use | Built for content pages: an app whose screens share state works against its islands |
| SvelteKit | Small bundles, mature on Workers | Can't use the site's React components or its editor |
| A second Worker at app.sulba.dev | Deploys apart from the site | A second Worker, domain and preview policy to set up in the dashboard, and a session of its own |

## Evidence

- [Cloudflare, Workers limits](https://developers.cloudflare.com/workers/platform/limits/) (updated October 12, 2026): Workers Free gives a request 10 ms of CPU time and an account 100,000 requests a day; waiting on network requests doesn't count; the average Worker uses about 2.2 ms a request, and work with server-side rendering typically 10 to 20 ms; a Worker can be 64 MiB on either plan.
- [Cloudflare, Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/): requests to static assets are free and unlimited.
- [Cloudflare, Redirects for static assets](https://developers.cloudflare.com/workers/static-assets/redirects/): a rule with status 200 proxies to another path on the site; the top-most matching rule applies, and redirects run before headers.
- [Cloudflare, Worker script routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/): with static assets and a Worker, an asset that matches is served first.
- [Cloudflare, Next.js applications, powered by Vite: introducing Vinext 1.0](https://blog.cloudflare.com/vinext-nextjs-on-vite/) (September 28, 2026).
- [Vercel, Fair use guidelines](https://vercel.com/docs/limits/fair-use-guidelines): Hobby teams are restricted to non-commercial personal use; commercial use needs Pro or Enterprise.
- [TanStack Router, Overview](https://tanstack.com/router/latest/docs/framework/react/overview): type-safe routes and navigation, nested layouts, route loaders, and typed, validated search parameters.
- Measured on this repository: the app's first page loads 336 kB of JavaScript, 109 kB compressed, and supabase-js comes after a session exists, as another 215 kB, 55 kB compressed. Served by `astro preview` in workerd, `/app/` and `/app/specs/42` answer 200 with the app's page, its script 200 as JavaScript, and `/app/assets/missing.js` 404.

## Why

The app is a long-lived page behind sign-in, the case client-side React is made for, and drawing it in the browser keeps its pages off the Worker's CPU, so Workers Free stays enough until there are customers to pay for more. Serving it from the site's Worker keeps one domain, one deploy and one session, and the components and editor the Academy already tests come with it.

The strongest case against it is Next.js's ecosystem and its familiarity to the engineers Sulba may hire. The app gives up server rendering, which helps pages search engines index, and those pages are the Academy's and the site's.

## Consequences

- Each build of the site builds the app too, so a change to either ships together.
- A route the app needs on the server must stay within 10 ms of CPU, or the Worker moves to Workers Paid, at $5 a month.
- A pull request that changes only the app runs no machine labs, as one that changes only courses, docs and tools runs only the labs it changes.

## Revisit when

A page of the app must be found by search engines, or a route the app needs on the server takes more than 10 ms of CPU a request.
