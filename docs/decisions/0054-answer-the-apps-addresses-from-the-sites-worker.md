# 54. Answer the app's addresses from the site's Worker, not from routing rules

- Status: accepted
- Date: 2026-10-28
- Amends: [47. Build the app in React, drawn in the browser and served by the site's Worker under /app/](0047-build-the-app-in-react-served-by-the-sites-worker.md)

## Context

Decision record 47 had `public/_redirects` answer every address under `/app/` with the app's page, except the app's own files, using two rules in this order: `/app/assets/* /app/assets/:splat 200`, then `/app/* /app/ 200`. Served by `astro preview` in workerd, the first rule served the app's files and the second answered everything else. On sulba.dev, every address under `/app/assets/` answered with the app's page, its script and stylesheet among them, so the browser wouldn't run the script and the app showed nothing.

Cloudflare's documentation says the top-most matching rule applies (decision record 47). sulba.dev didn't follow it for these two rules, and why isn't known. `wrangler deploy` uploads `_redirects` as text for Cloudflare to read, while workerd reads it with Miniflare's parser, so no local run can show which rule sulba.dev applies.

## Decision

- `public/_redirects` has no rule for `/app/`.
- In `wrangler.jsonc`, `run_worker_first` sends `/app/*` to the Worker before the static assets, except `/app/assets/*`.
- The app's files under `/app/assets/` are served as static assets, and a missing one answers 404.
- Every other address under `/app/` reaches the Worker. There, `src/pages/app/[...path].ts` answers with the app's page, which it fetches through the `ASSETS` binding.
- After each deploy of main, `.github/scripts/check-app.sh` opens an address of the app on sulba.dev as a browser opens a page, and asks for the script that page loads. The deploy job fails unless the script answers as JavaScript.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| `run_worker_first` for `/app/*` but `/app/assets/*`, and a route on the Worker that answers with the app's page (chosen) | No two rules match the same address, so the order Cloudflare reads them in doesn't matter; workerd runs the same rules and route locally | Every page load under `/app/` is a Worker request, and Workers Free allows 100,000 a day |
| Keep the two rules in `_redirects` (decision record 47) | The Worker runs no code for the app | sulba.dev answers the app's files with its page |
| A route on the Worker alone, with no `run_worker_first` | Nothing to set in `wrangler.jsonc` | A request a browser makes to open a page, with `Sec-Fetch-Mode: navigate`, that matches no file gets the site's 404 page from the static assets and never reaches the Worker |
| Build the app's files outside `/app/`, so one rule covers its pages without overlapping them | Keeps the Worker out | Vite writes the page beside its files, so the build would need asset paths of its own, and the page would still depend on how Cloudflare reads a rule |

## Evidence

- Measured on sulba.dev after the deploy of `dee0311`: `/app/`, `/app/acme/specs` and `/app/specs/42` answered 200 with the app's 570-byte page. So did `/app/assets/index-DgCPJyrp.js` (the page's script), `/app/assets/index-VfAgyBfm.css`, and `/app/assets/nope-23690.js`, a file that doesn't exist, each as `text/html`. A query string added to a script's address changed nothing.
- Measured in workerd (`astro preview`) on the same commit's build: the script answered 200 as `text/javascript`, and `/app/assets/missing.js` answered 404.
- Measured in workerd with a route on the Worker and no `run_worker_first`: `/app/nothing/here/at/all/` answered 200 with the app's page to a plain request, and 404 with the site's 404 page to the same request with `Sec-Fetch-Mode: navigate`.
- Measured in workerd with this change, both as a plain request and with `Sec-Fetch-Mode: navigate`:
  - `/app/`, `/app/acme`, `/app/acme/SPEC-3`, `/app/nothing/here/at/all/` and `/app/oauth/consent` answer 200 with the app's page, all with the same ETag and with `X-Robots-Tag: noindex`.
  - `/app` redirects to `/app/`.
  - The script answers 200 as `text/javascript`.
  - `/app/assets/missing.js` and `/nope/` answer 404 with the site's 404 page.
  - `/academy/` answers 200.
- [Wrangler 4.152.0](https://www.npmjs.com/package/wrangler/v/4.152.0), `wrangler-dist/cli.js`, read in this repository's `node_modules`:
  - On deploy, `_redirects` and `_headers` go up as text modules. A comment there says they are "parsed in Miniflare in dev and parsing is not required for deploy".
  - `run_worker_first` takes `true` or an array of rules. A rule starting with `!/` leaves those addresses to the static assets, and an array needs at least one rule that doesn't.
- [Miniflare 5.20261019.2-beta](https://www.npmjs.com/package/miniflare/v/5.20261019.2-beta), read in this repository's `node_modules`:
  - The asset worker, `dist/src/workers/assets/assets.worker.js`: `handleRedirects` takes the first matching rule, in the order the parsed rules are stored. The `assets_navigation_prefers_asset_serving` flag, on by default for compatibility dates after 2025-04-01, has a request with `Sec-Fetch-Mode: navigate` that matches no file answered by `not_found_handling` instead of reaching the Worker.
  - The router worker, `dist/src/workers/assets/router.worker.js`: it sends a request to the Worker first when a `run_worker_first` rule matches it.
- [@astrojs/cloudflare 14.4.2](https://www.npmjs.com/package/@astrojs/cloudflare/v/14.4.2), `dist/fetch.js` and `dist/entrypoints/image-passthrough-endpoint.js`, read in this repository's `node_modules`: the adapter reads bindings from `cloudflare:workers` and fetches files through `env.ASSETS`.

## Why

The app works on sulba.dev only if its files and its pages stop depending on how Cloudflare orders two rules that match the same address. With `run_worker_first`, every address under `/app/` goes to exactly one place: the static assets for its files, the Worker for everything else. workerd applies the same rules, so the end-to-end tests exercise the path production takes, and the check after each deploy covers what they can't see.

The strongest case against it is decision record 47's: the Worker now runs for every page load of the app. The route only asks the `ASSETS` binding for one file, and the app moves between its pages in the browser, so only a page opened or reloaded reaches the Worker.

## Consequences

- Each page opened or reloaded under `/app/` counts against Workers Free's 100,000 requests a day.
- Routing for `/app/` lives in `wrangler.jsonc` and the route, never in `_redirects`.
- When the check after a deploy fails, the deploy has already gone out, and the fix goes out in the next one.

## Revisit when

The app's page loads approach Workers Free's daily requests, or Cloudflare documents how it orders overlapping rules in `_redirects` and sulba.dev bears that out.
