# Working on Sulba

Rules for Claude Code in this repository. They come from the founder and override defaults.

## Hard rules

- Never commit, push, open pull requests or rewrite history. The founder reviews and commits every change. Work ends with every check passing and a drafted commit message for each task: one task per commit, an imperative subject under 50 characters, a body only when the reason isn't obvious, and the files that belong to it.
- Follow best practice without being asked: maintained libraries, strict types, tests for behaviour, no dead code. No filler in code, comments, docs or commit messages.
- Decide on evidence. A new architectural choice gets a record in `docs/decisions` with the options compared and the sources read. An accepted record is superseded, never rewritten.
- Secrets never enter the repository, issues or logs. They live in GitHub Actions secrets, Cloudflare Worker secrets, the Supabase dashboard or a gitignored `.dev.vars`. Never read `.dev.vars` or `.env` files.
- Only public keys reach the browser: the Supabase publishable key and the Turnstile site key.
- Learner data lives in Supabase, never in GitHub.

## Commands

| Command | What it does |
| --- | --- |
| `pnpm dev` | Runs the site at http://localhost:4321 in workerd |
| `pnpm lint` / `pnpm lint:fix` | Biome: formatting, lint rules, import order |
| `pnpm typecheck` | `astro check` at TypeScript's strictest settings |
| `pnpm test` | Vitest unit tests |
| `pnpm test:e2e` | Playwright end-to-end and axe accessibility tests, desktop and phone |
| `pnpm build` | Builds the site |

Run lint, typecheck, test and test:e2e before calling work done.

## How the project is set up

- `apps/web` is Astro 7 on the Cloudflare Worker `sulba` (`wrangler.jsonc`). Pages are built ahead of time; a route renders on the server only when it must (decision record 1).
- Astro sessions are off and images are optimised at build time, so a deploy creates no KV namespace and no Images binding.
- `public/_headers` sends `X-Robots-Tag: noindex` everywhere until launch (Phase 5). At launch it comes off sulba.dev only; preview and workers.dev addresses keep it.
- CI runs on every push. When it passes, `main` deploys to sulba.dev and other branches get a preview address. Branches named `renovate/*` are tested but not deployed.
- Dependencies are pinned to exact versions. pnpm refuses versions less than a day old and Renovate waits three days. TypeScript stays on 6 until `@astrojs/check` supports 7.
- GitHub Actions are pinned to commit SHAs with the version in a comment.
- The build phases (Phase 0 to Phase 6) are internal. Learners never see them.
- One course at a time: AI Engineering is built end to end before any other course starts. A language's editor support and Docker image arrive with the first session that uses it.

## Correctness

Wrong content is worse than no content. Never claim certainty you don't have. These checks happen behind the scenes: no page ever tells learners how content is checked or computed.

- Every number, table and chart a learner sees is produced by code that runs in CI.
- Every from-scratch build is tested against a reference implementation, such as PyTorch or NumPy, within a stated tolerance.
- A claim code can't check is verified against a primary source (a paper, the official documentation) that was opened and read, not recalled.
- Versions, model names, APIs and prices are pinned and dated, and re-checked before each release.
- Before a level goes public, it is reviewed again against live sources.

## Product rules

- Learner-facing copy reads like a real course product: plain topic titles, standard section names (Brief, Hints, Explanation, Solution, Tests, Chart, Review) and short, direct sentences. Never describe how the site is made. No coaxing or teaser lines.
- Every number a learner sees can be traced to its inputs on the same screen.
- No referral schemes of any kind.
- Data and API providers may be credited where their terms ask; teaching sources are not.
- The site's footer links to this repository's source, as the AGPL asks of a network service.

## On Windows

- Edit files with the editor tools, never by round-tripping text through PowerShell, which corrupts UTF-8.
- Files use LF line endings (`.gitattributes`). Never rewrite bytes across a folder tree.
