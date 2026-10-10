# Working on Sulba

Rules for Claude Code in this repository. They come from the founder and override defaults.

## Hard rules

- Work on a feature branch, never on `main`, and commit to it as you go. When every check passes and the work meets the standard, squash the branch into one commit, push it and open a pull request. One pull request does one task. The founder reviews and merges every pull request: never merge, push to `main` or rewrite its history.
- Commit messages have an imperative subject under 50 characters and a body only when the reason isn't obvious. Commits and pull request descriptions carry no attribution lines and no session links.
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

- `apps/web` is Astro 7 on the Cloudflare Worker `web` (`wrangler.jsonc`). Pages are built ahead of time; a route renders on the server only when it must (decision record 1).
- Astro sessions are off and images are optimised at build time, so a deploy creates no KV namespace and no Images binding.
- `public/_headers` sends `X-Robots-Tag: noindex` everywhere until launch (Phase 5). At launch it comes off sulba.dev only; preview addresses keep it.
- CI runs once for every pull request and every push to `main`. When it passes, `main` deploys to sulba.dev, the site's only address, and a pull request from this repository gets a Worker Preview on workers.dev, which `preview-cleanup.yml` deletes when its branch is deleted. Dependency updates (`renovate/*`) and pull requests from forks are tested but not deployed.
- Cloudflare Access ("Previews only", set in the dashboard) puts every preview address behind sign-in, and sulba.dev stays public (decision record 9). Worker Previews need `preview_urls` on. Never turn it on in a Cloudflare account without that Access policy: it brings back every old preview address, and those can't be deleted.
- Dependencies are pinned to exact versions. pnpm refuses versions less than a day old and Renovate waits three days. TypeScript stays on 6 until `@astrojs/check` supports 7.
- GitHub Actions are pinned to commit SHAs with the version in a comment.
- The build phases (Phase 0 to Phase 6) are internal. Learners never see them.
- The pictures in `brand` are drawn by `pnpm brand` (`apps/web/scripts/brand.ts`) from the mark, the avatar shapes and the design tokens. Change the script and run it again; never edit a picture by hand.
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

## Documentation

- Each document has one purpose and one home: rules in this file, running and contributing in the README and CONTRIBUTING, decisions in `docs/decisions`. A fact lives in one place; other documents link to it.
- Documents cover the app, its architecture, principles and rules. Research notes, session history and explorations stay out; research appears only as a decision record's sources.
- Documents state what is decided, not what was ruled out. Options that were weighed appear only in the decision record that compared them.
- When the code or a decision changes, every document that mentions it changes in the same commit, and what no longer applies is deleted. Accepted decision records are the exception: they are superseded.
- A document is written when the thing it describes exists.

## On Windows

- Edit files with the editor tools, never by round-tripping text through PowerShell, which corrupts UTF-8.
- Files use LF line endings (`.gitattributes`). Never rewrite bytes across a folder tree.
