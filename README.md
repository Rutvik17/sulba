# Sulba

Sulba is the school of the AI era. Engineers learn the fundamentals by hand, then catch what an AI assistant gets wrong and ship code that works in real use. Every lab runs as Build, Catch and Ship, each stage checked by real tests, which run in the browser or on the learner's own machine. The first course, AI Engineering, is in development.

## Run it locally

You need [Node.js 24](https://nodejs.org/) and [pnpm 12](https://pnpm.io/installation), [uv](https://docs.astral.sh/uv/getting-started/installation/) for the Python checks, and [Docker](https://docs.docker.com/get-started/get-docker/) for the database tests.

```sh
pnpm install
pnpm dev
```

The site runs at http://localhost:4321 in workerd, the runtime Cloudflare uses in production, and http://localhost:4321/gallery/ shows every component in each of its states. Sign-in uses the hosted Supabase project, which sends a sign-in back to loopback addresses but not to `localhost` by name, so open http://127.0.0.1:4321 to sign in while developing. The contact form sends mail only with its four secrets in a gitignored `apps/web/.dev.vars` ([decision record 12](docs/decisions/0012-send-contact-messages-through-resend-after-turnstile.md)); without them it answers that it can't send.

| Command | What it does |
| --- | --- |
| `pnpm dev` | Runs the site locally |
| `pnpm build` | Builds the site |
| `pnpm lint` | Checks formatting and lint rules with Biome |
| `pnpm lint:fix` | Fixes formatting and safe lint issues |
| `pnpm lint:python` | Checks the Python code, course code included, with Ruff |
| `pnpm typecheck` | Type-checks the code |
| `pnpm test` | Runs the unit tests |
| `pnpm test:python` | Runs the lab's Python tests in CPython |
| `pnpm check:content` | Checks every course, and runs every stage in Pyodide and CPython |
| `pnpm check:references` | Records every lab's references again with the library its `make.py` pins, and compares them with the files |
| `pnpm check:machine` | Runs every lab that runs on the learner's machine from its download, through `uv run sulba.py`, as a learner would; with `--model`, starts each model a lab serves and asks it a question |
| `pnpm test:db` | Runs the database's migrations in a local Supabase, and the tests of its row-level security |
| `pnpm --filter @sulba/data types` | Writes the database's TypeScript types from the local Supabase |
| `pnpm test:e2e` | Runs the end-to-end and accessibility tests in Chromium, Firefox and WebKit |
| `pnpm brand` | Draws the profile pictures and banners in `brand`, and the site's icons |

Before the first `pnpm test:e2e`, install the browsers with `pnpm --filter @sulba/web exec playwright install chromium firefox webkit`.

## Repository

| Path | Contents |
| --- | --- |
| `apps/web` | The site: Astro on Cloudflare Workers |
| `packages/ui` | Design tokens, base styles and components |
| `packages/editor` | The code editor |
| `packages/lab` | Runs a session's tests: in the browser with Pyodide, or in CPython |
| `packages/content` | Reads and checks the courses |
| `packages/data` | The database, its migrations and tests, and the site's connection to Supabase |
| `brand` | Profile pictures and banners for Sulba's accounts on other sites |
| `courses` | Course content, laid out as [its README](courses/README.md) describes |
| `tools` | Scripts that build course data |
| `docs/decisions` | Architecture decision records |
| `.github/workflows` | CI and deploys |

Every pull request runs the checks, and so does every push to `main`. When they pass, `main` deploys to sulba.dev and each pull request gets its own private preview address.

## Licences

- Code: [GNU Affero General Public License v3.0 only](LICENSE)
- Course content in `courses/`: [all rights reserved](courses/LICENSE)
- The Sulba name and logo are not licensed for reuse.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md). To report a vulnerability, follow [SECURITY.md](SECURITY.md) instead of opening an issue.
