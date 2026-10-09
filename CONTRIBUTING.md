# Contributing

Sulba is early in development. Issues are welcome. For anything larger than a small fix, open an issue before a pull request, so the approach is agreed first.

## Setup

Follow [Run it locally](README.md#run-it-locally) in the README.

## Before you open a pull request

Run the same checks as CI:

```sh
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
```

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
