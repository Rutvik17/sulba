# Contributing

Sulba is early in development. Issues are welcome. For anything larger than a small fix, open an issue before a pull request, so the approach is agreed first.

## Setup

Follow [Run it locally](README.md#run-it-locally) in the README.

## Before you open a pull request

Run the same checks as CI:

```sh
pnpm lint
pnpm lint:python
pnpm typecheck
pnpm test
pnpm test:python
pnpm check:content
```

CI runs the end-to-end and accessibility tests on the first of each month, and when started by hand from the Actions tab. Pull requests and pushes to `main` don't run them.

## Screenshots

The gallery at `/gallery/` shows every component in each of its states. CI's Screenshots job compares it with the pictures in `apps/web/screenshots`. Browsers draw text a little differently on every system, so those pictures are taken only in Playwright's Linux image, in CI, and the job doesn't run on your machine.

When a change alters the look, the job fails and attaches the new screenshots to the run as the `screenshots` artifact, with a report that shows each difference. If the change is intended, download them into the app and commit them:

```sh
gh run download <run id> --name screenshots --dir apps/web
```

The pull request then shows each changed picture beside the old one.

## Commits

- One task per commit.
- A subject line under 50 characters, in the imperative: "Add the 404 page", not "Added the 404 page".
- A body after a blank line, when the reason for the change isn't clear from the diff.

## Code

- Biome formats and lints the code; `pnpm lint:fix` applies its fixes.
- TypeScript runs with its strictest settings. Fix an error rather than silencing it.
- Prefer clear names to comments. Write a comment only to explain why something is done.
- Changing an architecture decision needs a new record in [docs/decisions](docs/decisions/README.md).

## Licensing

Code contributions are accepted under AGPL-3.0-only. Course content in `courses/` is all rights reserved and doesn't take outside contributions; to report a mistake in a lesson, open an issue.
