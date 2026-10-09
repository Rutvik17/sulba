# 2. Use Astro 7, with React for the interactive parts

- Status: accepted
- Date: 2026-10-08

## Context

Most of Sulba is content: hundreds of lessons and problems. Its interactive parts (the workspace, review, the dashboard and discussions) each live on one page. The framework must run on Cloudflare at $0 (record 3) and work on Windows, where Sulba is developed.

## Decision

Astro 7, with React components for the workspace, review, the dashboard and discussions.

## Options

| | Astro 7 | Next.js 16 | React Router 8 |
| --- | --- | --- | --- |
| Mobile sites passing Core Web Vitals, July 2026 | 69.81% | 33.89% | Not reported |
| Developer satisfaction, State of JS 2025 | Highest of all meta-frameworks | 39 points behind Astro, and falling | Write-in only |
| Learning platforms using it (checked 8 October 2026) | None of those checked | LeetCode, Codecademy, Brilliant, DataCamp, Educative, CodeCrafters | roadmap.sh |
| On Cloudflare Workers | First-class: Cloudflare took over the Astro team in January 2026 | Through OpenNext, a community adapter; "Windows full support is not guaranteed" | Official guide, but prerendering is "not currently supported" with Cloudflare's plugin |
| Course content | Content collections with schemas built in | A third-party content layer | A third-party content layer |
| Caching server-rendered pages | Route caching (stable in 7.0), with an experimental Cloudflare CDN provider | ISR and `use cache`, both supported by OpenNext | Written by hand |
| JavaScript on a lesson page with nothing interactive | None | React and its router | React and its router |

## Evidence

- The speed figures are the HTTP Archive's July 2026 field data ([via Straffe Sites](https://straffesites.com/en/blog/astro-vs-next-js)). Part of the gap comes from what each framework is used for, since content sites tend to choose Astro, so it shows a direction rather than proving a cause. The mechanism is the one Google describes: less JavaScript, faster pages.
- Satisfaction: [State of JS 2025](https://2025.stateofjs.com/en-US/libraries/meta-frameworks/).
- Cloudflare support: [OpenNext for Cloudflare](https://opennext.js.org/cloudflare), [React Router on Cloudflare](https://developers.cloudflare.com/workers/framework-guides/web-apps/react-router/), [Astro on Cloudflare](https://developers.cloudflare.com/workers/framework-guides/web-apps/astro/) and [Cloudflare acquires the Astro team](https://pulse2.com/cloudflare-acquires-astro/).
- Astro 7 builds 15 to 61% faster than Astro 6 ([Astro 7](https://astro.build/blog/astro-7/)).

## Why

Content is Sulba's largest surface, and Astro sends no JavaScript to pages that don't need it. It runs on Cloudflare at $0 and on Windows. Each interactive part lives on one page, which is what islands are for, and Astro's client router with `transition:persist` keeps an island alive across navigations where an app-like feel is wanted ([view transitions](https://docs.astro.build/en/guides/view-transitions/)).

Next.js is the category's standard, and more contributors know it. That outweighs Astro only on Vercel. On Cloudflare it depends on a community adapter that doesn't guarantee Windows, and Vercel's free plan forbids commercial use (record 3). TanStack Start was still in beta when State of JS 2025 ran, too new to build the product on.

## Consequences

Fewer ready-made app patterns than Next.js, and a framework fewer contributors know. Components are plain React, and the lab, editor, data and content packages are plain TypeScript, so a move to another framework would replace only the routing shell.

## Revisit when

Most screens become app-like feeds, for example if the social layer grows.
