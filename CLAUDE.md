# Working on Sulba

Rules for Claude Code in this repository. They come from the founder and override defaults.

## Hard rules

- Work on a feature branch, never on `main`, and commit to it as you go. When every check passes and the work meets the standard, squash the branch into one commit, push it and open a pull request. One pull request builds one lab end to end, with all its stages. Any other work, such as setup or a platform feature, takes one pull request per task. The founder reviews and merges every pull request: never merge, push to `main` or rewrite its history.
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
| `pnpm lint:python` | Ruff on the Python code: the lab's, the courses' and the tools' |
| `pnpm typecheck` | `astro check` at TypeScript's strictest settings |
| `pnpm test` | Vitest unit tests |
| `pnpm test:python` | The lab's Python tests, in CPython through uv |
| `pnpm check:content` | Every course's files against their schemas, and every stage in Pyodide and CPython |
| `pnpm test:e2e` | Playwright end-to-end and axe accessibility tests in Chromium, Firefox and WebKit, on desktop and phone |
| `pnpm build` | Builds the site |

Run lint, lint:python, typecheck, test, test:python and check:content before calling work done. On Windows, run the Python ones in Docker if uv isn't installed.

End-to-end tests are written with each feature, and run only when the founder asks. CI runs them on the first of each month and when started by hand (`e2e.yml`), never on a pull request or a push to `main`; fix anything a run shows broken in the next pull request.

## How the project is set up

- `apps/web` is Astro 7 on the Cloudflare Worker `web` (`wrangler.jsonc`). Pages are built ahead of time; a route renders on the server only when it must (decision record 1).
- Astro sessions are off and images are optimised at build time, so a deploy creates no KV namespace and no Images binding.
- `public/_headers` sends `X-Robots-Tag: noindex` everywhere until launch (Phase 5). At launch it comes off sulba.dev only; preview addresses keep it.
- CI runs once for every pull request and every push to `main`. When it passes, `main` deploys to sulba.dev, the site's only address, and a pull request from this repository gets a Worker Preview on workers.dev, which `preview-cleanup.yml` deletes when its branch is deleted. Dependency updates (`renovate/*`) and pull requests from forks are tested but not deployed.
- The contact form posts to `/api/contact`, which checks the Turnstile token and sends the message with Resend (decision record 12). Its four secrets are Worker secrets; without them it answers 503. Tests stand in for `/api/contact` and Turnstile, so no test ever sends mail.
- Cloudflare Web Analytics is set in the dashboard, so it's in no file here and local tests never see it. Cloudflare adds its script to every page except for visitors in the EU (Web Analytics on "Enable, excluding visitor data in the EU") and in the UK, Norway, Iceland, Liechtenstein and Switzerland (a Configuration Rule that disables Real User Monitoring), as decision record 13 sets out. Workers Logs are on too (`observability` in `wrangler.jsonc`).
- Cloudflare Access ("Previews only", set in the dashboard) puts every preview address behind sign-in, and sulba.dev stays public (decision record 9). Worker Previews need `preview_urls` on. Never turn it on in a Cloudflare account without that Access policy: it brings back every old preview address, and those can't be deleted.
- Dependencies are pinned to exact versions. pnpm refuses versions less than a day old and Renovate waits three days. TypeScript stays on 6 until `@astrojs/check` supports 7.
- GitHub Actions are pinned to commit SHAs with the version in a comment.
- Components live in `packages/ui`, a folder each: a CSS Module for the look, and a React component that takes its behaviour from React Aria Components (decision record 11). Astro pages put a component's classes on native elements and load no JavaScript; only a page with a React island loads React.
- `packages/editor` is the code editor: CodeMirror 6 with Python, Sulba's colour theme and 14 named after popular editor themes, and Ruff's checks and formatting in a Web Worker (decision record 14).
- The gallery at `/gallery/` shows every component in each of its states. `astro dev`, the end-to-end tests and previews have it; sulba.dev doesn't (`apps/web/gallery.ts`). A new component, or a new state, joins the gallery and its screenshot tests in the same pull request.
- CI's Screenshots job compares the gallery with the pictures in `apps/web/screenshots`, taken in Playwright's Linux image; they never run on Windows. When the look changes on purpose, commit the new screenshots the failed job attaches (CONTRIBUTING.md).
- `packages/lab` runs a session's tests and speaks one protocol for every runner (decision record 5): files and tests go in, a result per test comes out. In the browser, Pyodide runs in a Web Worker, and a run past the time limit is stopped by ending the worker. Both Pyodide and CPython call the same pytest plugin (`python/sulba_runner.py`), and the fixtures in `fixtures/` must give the same results in each. Checks outside a browser run requests through `src/node.ts`: in Pyodide, or in CPython through uv.
- `pnpm --filter @sulba/lab pyodide`, which `pnpm test` runs first, puts Pyodide's files together in `packages/lab/pyodide`: its core from npm, and each package's wheel, checked against the sha256 in Pyodide's lock file. The site serves them at `/pyodide/<version>/` (`apps/web/pyodide.ts`), cached for good. The CPython packages in `packages/lab/python/uv.lock` are pinned to the versions Pyodide ships, and a test fails when they differ, so Renovate leaves them alone.
- Formulas in a course's prose are TeX, which Temml renders to MathML at build time, set in Noto Sans Math from `packages/ui/src/fonts` (decision record 15). Numbers in prose come from the stage's `figures.py`, never typed. Both the content check and the build fail on a formula that doesn't render, a figure missing or never shown, figures that differ between Pyodide and CPython, or a character the math font can't draw.
- Courses are files in `courses/`, laid out as `courses/README.md` describes (decision record 7). `packages/content` reads them, checks them against their schemas, and builds each stage's runs: a stage's solution must pass its own and every earlier stage's tests, a Build stage's starter must fail at least one, and a Catch stage's problems must each be found by one hidden check (`courses/README.md`).
- Each lab has a page at `/<course>/<module>/<lab>/`, built from `courses/` through a content collection (`apps/web/src/lib/labs.ts`). Its workspace is a React island that renders only in the browser: it keeps each stage's code, the stages passed and each finished Catch review in browser storage, opens a stage once the one before is passed, and runs the tests with `packages/lab`. A build with `SULBA_COURSES` set reads courses from that folder instead; the end-to-end tests use the content package's fixture course.
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
- The site never says its code is open source, and it doesn't link to this repository.
- The Privacy Policy and the Terms describe the site as built. A change to what the site collects, keeps in the browser or sends to a provider updates the Privacy Policy, and its date, in the same pull request.

## Documentation

- Each document has one purpose and one home: rules in this file, running and contributing in the README and CONTRIBUTING, decisions in `docs/decisions`. A fact lives in one place; other documents link to it.
- Documents cover the app, its architecture, principles and rules. Research notes, session history and explorations stay out; research appears only as a decision record's sources.
- Documents state what is decided, not what was ruled out. Options that were weighed appear only in the decision record that compared them.
- When the code or a decision changes, every document that mentions it changes in the same commit, and what no longer applies is deleted. Accepted decision records are the exception: they are superseded.
- A document is written when the thing it describes exists.

## On Windows

- Edit files with the editor tools, never by round-tripping text through PowerShell, which corrupts UTF-8.
- Files use LF line endings (`.gitattributes`). Never rewrite bytes across a folder tree.
