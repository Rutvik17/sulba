# 9. Keep branch previews behind Cloudflare Access

- Status: accepted
- Date: 2026-10-09

## Context

Every branch gets a Worker Preview (record 3). Preview addresses are public by default, and some can't be deleted. Worker Previews need Version URLs on, which also brings back every earlier Version URL and alias. Cloudflare keeps the 1,000 most recent aliases and gives no way to delete them. A Preview's own deployment address kept serving after the Preview was deleted. Sulba publishes no address it can't remove or make private.

## Decision

Cloudflare Access protects the previews of every Worker in the account ("Previews only"). Every preview address asks for sign-in, and only the founder's email address is allowed. sulba.dev stays public. Access is turned on in the dashboard before Version URLs come back on.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Previews behind Access (chosen) | Every preview address is private, including the ones that can't be deleted; CI and deploys are unchanged | Zero Trust onboarding asks for payment details, even on the Free plan |
| Public previews | Nothing to set up | Addresses that can't be deleted stay public |
| No previews: deploy only `main` | No preview addresses at all | A branch is only seen locally, and turning Version URLs on later brings the old addresses back, public |

## Evidence

[Cloudflare Access for Workers](https://developers.cloudflare.com/workers/configuration/cloudflare-access/), [Workers protected by Access](https://blog.cloudflare.com/workers-protected-by-access/), [Previews](https://developers.cloudflare.com/workers/previews/), [Version URLs](https://developers.cloudflare.com/workers/versions-and-deployments/version-urls/), [Access pricing](https://www.cloudflare.com/sase/products/access/) and [Create a Zero Trust organization](https://developers.cloudflare.com/learning-paths/cybersafe/account-creation/create-zero-trust-org/).

Tested on 9 October 2026. After `wrangler preview delete`, the Preview's branch address returned 404, but its deployment address still served. With `preview_urls` off, Worker Previews returned error 1042.

Checked on 9 October 2026 with Access on and Version URLs back on. sulba.dev returned 200 and `web.sulba.workers.dev` 404. Every kind of preview address redirected to the Access sign-in: a Worker Preview's branch and deployment addresses, an old alias, Version URLs including the current production version's, and a preview name that doesn't exist.

## Why

Access is the only option that makes every preview address private, including the ones Cloudflare can't delete. It keeps branch previews for checking a change on a real phone before it merges. The Zero Trust Free plan costs $0 for up to 50 users, and Sulba needs one.

## Consequences

Opening a preview takes a one-time PIN sent by email. Access is set in the dashboard, not in the repository, so a new Cloudflare account must set it up again before Version URLs go on. Previews still count toward Cloudflare's limits: on the Free plan, 100 Previews per Worker and 100 deployments per Preview, with the oldest deleted automatically.

## Revisit when

Cloudflare lets a preview and all of its addresses be deleted, or Sulba needs more than 50 people signing in to Zero Trust.
