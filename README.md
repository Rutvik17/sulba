# Sulba

Sulba is an online school for software engineers. Each session is a coding task checked by real tests, which run in the browser or on the learner's own machine. The first course, AI Engineering, is in development.

## Run it locally

You need [Node.js 24](https://nodejs.org/) and [pnpm 12](https://pnpm.io/installation).

```sh
pnpm install
pnpm dev
```

The site runs at http://localhost:4321 in workerd, the runtime Cloudflare uses in production.

| Command | What it does |
| --- | --- |
| `pnpm dev` | Runs the site locally |
| `pnpm build` | Builds the site |
| `pnpm lint` | Checks formatting and lint rules with Biome |
| `pnpm lint:fix` | Fixes formatting and safe lint issues |
| `pnpm typecheck` | Type-checks the code |
| `pnpm test` | Runs the unit tests |
| `pnpm test:e2e` | Runs the end-to-end and accessibility tests in Chromium |

Before the first `pnpm test:e2e`, install the browser with `pnpm --filter @sulba/web exec playwright install chromium`.

## Repository

| Path | Contents |
| --- | --- |
| `apps/web` | The site: Astro on Cloudflare Workers |
| `courses` | Course content |
| `docs/decisions` | Architecture decision records |
| `.github/workflows` | CI and deploys |

Every push runs the checks. When they pass, `main` deploys to sulba.dev and every other branch gets its own private preview address.

## Licences

- Code: [GNU Affero General Public License v3.0 only](LICENSE)
- Course content in `courses/`: [all rights reserved](courses/LICENSE)
- The Sulba name and logo are not licensed for reuse.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md). To report a vulnerability, follow [SECURITY.md](SECURITY.md) instead of opening an issue.
