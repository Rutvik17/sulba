# Sulba

Sulba is the school of the AI era. Engineers learn the fundamentals by hand, then build with AI: they design the system, direct the assistant and review what it writes. Each session is checked by real tests, which run in the browser or on the learner's own machine. The first course, AI Engineering, is in development.

## Run it locally

You need [Node.js 24](https://nodejs.org/) and [pnpm 12](https://pnpm.io/installation).

```sh
pnpm install
pnpm dev
```

The site runs at http://localhost:4321 in workerd, the runtime Cloudflare uses in production. The contact form sends mail only with its four secrets in a gitignored `apps/web/.dev.vars` ([decision record 12](docs/decisions/0012-send-contact-messages-through-resend-after-turnstile.md)); without them it answers that it can't send.

| Command | What it does |
| --- | --- |
| `pnpm dev` | Runs the site locally |
| `pnpm build` | Builds the site |
| `pnpm lint` | Checks formatting and lint rules with Biome |
| `pnpm lint:fix` | Fixes formatting and safe lint issues |
| `pnpm typecheck` | Type-checks the code |
| `pnpm test` | Runs the unit tests |
| `pnpm test:e2e` | Runs the end-to-end and accessibility tests in Chromium |
| `pnpm brand` | Draws the profile pictures and banners in `brand` |

Before the first `pnpm test:e2e`, install the browser with `pnpm --filter @sulba/web exec playwright install chromium`.

## Repository

| Path | Contents |
| --- | --- |
| `apps/web` | The site: Astro on Cloudflare Workers |
| `brand` | Profile pictures and banners for Sulba's accounts on other sites |
| `courses` | Course content |
| `docs/decisions` | Architecture decision records |
| `.github/workflows` | CI and deploys |

Every pull request runs the checks, and so does every push to `main`. When they pass, `main` deploys to sulba.dev and each pull request gets its own private preview address.

## Licences

- Code: [GNU Affero General Public License v3.0 only](LICENSE)
- Course content in `courses/`: [all rights reserved](courses/LICENSE)
- The Sulba name and logo are not licensed for reuse.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md). To report a vulnerability, follow [SECURITY.md](SECURITY.md) instead of opening an issue.
