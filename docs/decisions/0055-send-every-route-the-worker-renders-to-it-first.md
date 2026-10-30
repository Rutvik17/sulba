# 55. Send every route the Worker renders to it first

- Status: accepted
- Date: 2026-10-30
- Amends: [54. Answer the app's addresses from the site's Worker, not from routing rules](0054-answer-the-apps-addresses-from-the-sites-worker.md)

## Context

Decision record 54 set `run_worker_first` in `wrangler.jsonc` to `/app/*` but `/app/assets/*`, so the Worker answers the app's addresses. Once it deployed, every other route the Worker renders stopped working on sulba.dev, in workerd the same way:

- `/mcp` and `/.well-known/oauth-protected-resource/mcp` answered the site's 404 page to a GET and 405 to a POST, so no agent could connect.
- `/api/contact` and `/api/results` answered 405, so the contact form couldn't send and no CI run's report could arrive.

Once `run_worker_first` lists any rules, Cloudflare's router sends a request the rules don't name to the static assets. With `not_found_handling` set to `404-page`, the assets answer every address, so the Worker never runs. The end-to-end tests that would have caught this, such as the contact form's, weren't run before decision record 54 merged.

## Decision

- `run_worker_first` names every route the Worker renders: `/app/*` but `/app/assets/*`, `/api/*`, `/mcp` and `/.well-known/oauth-protected-resource/*`.
- A unit test, `apps/web/src/worker-first.test.ts`, reads `wrangler.jsonc` and every page and endpoint in `src/pages`, and fails when a route that renders on the Worker (`prerender = false`) isn't one of those addresses, or when a page built ahead of time is. CI runs it on every pull request.
- The check after each deploy of main (`.github/scripts/check-app.sh`) also asks sulba.dev for the MCP server's metadata, which only the Worker writes, and fails unless it answers as JSON.
- An end-to-end test asks for the MCP server's metadata and sends it a request without a token, and expects the Worker's 401.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Name every route the Worker renders in `run_worker_first`, and test the list against `src/pages` (chosen) | Pages built ahead of time and unknown addresses never reach the Worker, so they cost no requests; the test fails the pull request that adds a route without its address | The list and the routes live in two places, joined by the test |
| `run_worker_first` set to `true` | No list to keep | Every request reaches the Worker, the site's pages and files included, against Workers Free's 100,000 a day |
| `not_found_handling` set to `none` | An address with no file reaches the Worker, so new routes need no list | Every unknown address becomes a Worker request, and the site's 404 page is drawn by the Worker rather than served as a file |
| Revert decision record 54 | The routes work again | The app is blank again on sulba.dev |

## Evidence

- Measured on sulba.dev after the deploy of `fbe2b00` (decision record 54):
  - `GET /.well-known/oauth-protected-resource/mcp` and `GET /mcp` answered 404 with the site's 404 page.
  - `POST /mcp`, `POST /api/contact` and `POST /api/results` answered 405 with no `Allow` header, which the Worker's own routes always send.
  - Before that deploy, `/mcp` answered 401 and the metadata 200 as JSON.
- Measured in workerd (`astro preview`) on the same build: the same 404s and 405s.
- Measured in workerd with this change, as a plain request and as a browser opening a page:
  - The metadata answers 200 as JSON, `/mcp` 401 to a GET and a POST, `POST /api/contact` with an empty body 400, and `POST /api/results` 503 without the secret key, each from the Worker.
  - `/app/acme` answers 200 with the app's page, `/app/assets/missing.js` 404, `/academy/` and `/privacy/` 200, and `/nope/` 404.
- [Miniflare 5.20261019.2-beta](https://www.npmjs.com/package/miniflare/v/5.20261019.2-beta), read in this repository's `node_modules`:
  - The router worker, `dist/src/workers/assets/router.worker.js`, sends a request that matches no `run_worker_first` rule to the assets when they can answer it. A rule's `*` stands for any characters, `/` among them.
  - The asset worker, `dist/src/workers/assets/assets.worker.js`, sets `not_found_handling` aside when deciding whether it can answer, unless routing rules exist (`has_static_routing`) or the request opens a page. In those cases the 404 page counts as an answer.
- The unit test, run against decision record 54's `wrangler.jsonc`, fails and names `/mcp`, `/api/contact`, `/api/results` and `/.well-known/oauth-protected-resource/mcp`. It passes against this change.

## Why

The routes the Worker renders are few and change rarely, and the test ties each one to the list in the same pull request, so a route can't ship unreachable again. Naming them keeps every other address off the Worker: pages, files and unknown addresses stay free and fast.

The strongest case against it is the second place to edit when a route is added. The test makes forgetting it a failed pull request rather than a broken site.

## Consequences

- A new route that renders on the Worker needs its address in `run_worker_first`, or the unit test fails.
- The check after each deploy covers the app's page, its script and the MCP server, the addresses whose routing only sulba.dev can show.
- A change to how the site's addresses are routed runs the whole end-to-end suite, not only the app's files.

## Revisit when

A route the Worker renders needs an address `run_worker_first` can't name, or the Worker's daily requests near Workers Free's limit.
