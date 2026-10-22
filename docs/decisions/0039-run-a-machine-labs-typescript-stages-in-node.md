# 39. Run a machine lab's TypeScript stages in Node, pinned by the runner

- Status: accepted
- Date: 2026-10-22

## Context

Intermediate's Shipping full stack module puts the help desk's agent behind a web app, and its fourth lab is the app's front end in TypeScript: a typed client for the desk's API, the reply's event stream read from `fetch`, messages put on the page without `innerHTML`, and a dashboard of cost and latency. Every stage so far is Python, run with pytest in Pyodide or, for a lab that runs on the learner's machine, in CPython from the lab's download (decision record 28). A TypeScript stage needs a runtime that runs TypeScript, a type checker, a page's DOM for its tests, and its packages pinned, on the six systems machine labs run on, Windows, macOS and Linux each on x86-64 and Arm, with nothing for the learner to install but uv. Its results must come back as a Python run's do: one per test, with its id, the value it expected and the one it got, and the line of the learner's code where an error was raised.

## Decision

- **Runtime:** Node.js 24.22.1, the build nodejs.org publishes for each of the six systems. `sulba_runner.py` pins each by its size and sha256 and fetches it into `sulba` in the learner's cache folder the first time a TypeScript run needs it, as `sulba_fixtures.py` fetches pgvector on Linux. Node runs a `.ts` file by stripping its types.
- **Packages:** a lab whose stages are TypeScript has a `package.json`, a `package-lock.json` and a `tsconfig.json` in its project, and every run has the three beside the learner's files. The runner installs the lock's packages with `npm ci --ignore-scripts`, which runs no package's install scripts, once, into a folder of the cache folder named for the two files, and runs each session in a folder inside it, where Node and tsc find `node_modules`.
- **Types:** tsc, the TypeScript the lab's lock pins, checks the session's files as `tsconfig.json` includes them before any test runs. Its first error is the run's problem, with every error it found in the run's output, as a Python file's syntax error is.
- **Tests:** a test file is `<name>.test.ts`, run by Node's own test runner with a reporter of the runner's, `sulba_reporter.mjs`, which writes each result as a line of JSON. A test's id starts its name. Tests import the learner's files through `package.json`'s `imports`, as `#statement.ts`, so a test runs the same from `tests/`, `tests/checks/` or the folder a later stage's runs put it in.
- **The browser:** a lab whose TypeScript makes a page has a `tsconfig.build.json` in its project, and `uv run sulba.py build` compiles it to JavaScript with the same tsc, which `pnpm check:machine` runs on the stages' solutions.
- **Where:** only a lab that runs on the learner's machine. A run with tests in both languages runs each with its own runner and gives both results.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Node's own builds, pinned and fetched by the runner (chosen) | The current release of Node 24, a security release, on all six systems; checked by size and sha256, as the runner's other fetches are; one program for npm, tsc and the tests | 31 to 54 MB to fetch once on each system; the pins move by hand |
| nodejs-wheel from PyPI, in the lab's project | uv installs and locks it with the project's Python packages | An "unoffical Node.js package"; its newest release is 24.19.0, four releases behind 24.22.1, the security release of 20 October 2026 |
| Deno from PyPI, in the lab's project | One program that runs TypeScript and has its own `deno test` and `deno check`, which uv installs | 2.9.8 has wheels for macOS and Linux on x86-64 and Arm, and for Windows on x86-64 alone, so none for Windows on Arm |
| Node the learner installs | Nothing to fetch | Each learner has their own version, and one more install before the first stage |
| Vitest in place of Node's test runner | "a next generation testing framework powered by Vite", which reads a project's Vite settings | "Vitest requires Vite >=v6.4.0 and Node >=v22.12.0": more packages in every TypeScript lab, where Node's runner comes with Node |
| Type errors as a test, as `typecheck` is for Python (decision record 22) | A stage can pass with a type error it doesn't test | Node runs code that tsc refuses, so tests can pass on a file that doesn't compile |

## Evidence

- Node's [index of releases](https://nodejs.org/dist/index.json) lists v24.22.1, Krypton, on 2026-10-20 with `security: true`; its [previous releases page](https://nodejs.org/en/about/previous-releases): "Production applications should only use Active LTS or Maintenance LTS releases." [SHASUMS256.txt for v24.22.1](https://nodejs.org/dist/v24.22.1/SHASUMS256.txt) gives the sha256 of each of the six archives the runner pins.
- Node's [TypeScript page](https://nodejs.org/docs/latest-v24.x/api/typescript.html): "v24.12.0 Type stripping is now stable." "By default Node.js will execute TypeScript files that contains only erasable TypeScript syntax. Node.js will replace TypeScript syntax with whitespace, and no type checking is performed." "Node.js ignores tsconfig.json files".
- Node's [test runner page](https://nodejs.org/docs/latest-v24.x/api/test.html): its reporters' "exact output ... is subject to change between versions of Node.js, and should not be relied on programmatically. If programmatic access to the test runner's output is required, use the events emitted by the <TestsStream>", and "--test-reporter can be used to specify a path to custom reporter." With "--test-isolation=process (the default), each test file runs in a separate child process"
- Node's [packages page](https://nodejs.org/docs/latest-v24.x/api/packages.html): "there is a package "imports" field to create private mappings that only apply to import specifiers from within the package itself. Entries in the "imports" field must always start with # to ensure they are disambiguated from external package specifiers."
- npm's [`npm ci`](https://docs.npmjs.com/cli/v11/commands/npm-ci): "The project must have an existing package-lock.json or npm-shrinkwrap.json. If dependencies in the package lock do not match those in package.json, npm ci will exit with an error, instead of updating the package lock." Of `ignore-scripts`: "If true, npm does not run scripts specified in package.json files."
- TypeScript's [typeRoots](https://www.typescriptlang.org/tsconfig/typeRoots.html): "Packages in node_modules/@types of any enclosing folder are considered visible", so tsc finds `@types/node` from a session inside the packages' folder.
- PyPI's JSON for [nodejs-wheel](https://pypi.org/project/nodejs-wheel/): 24.19.0, uploaded 2026-08-19, described as "unoffical Node.js package"; Node's index lists 24.20.0, 24.21.0, 24.22.0 and 24.22.1 after it. For [deno](https://pypi.org/project/deno/): 2.9.8, "Python redistribution of Deno binaries", with wheels for macOS on x86-64 and arm64, manylinux on x86-64 and aarch64, and `win_amd64`. Deno's [installation page](https://docs.deno.com/runtime/getting_started/installation/) lists `deno test` and `deno check` among its commands.
- [Vitest's guide](https://vitest.dev/guide/): "Vitest (pronounced as "veetest") is a next generation testing framework powered by Vite", "Vitest reads your vite.config.* by default", and "Vitest requires Vite >=v6.4.0 and Node >=v22.12.0".
- A spike ran Node 24.22.1 from nodejs.org, with TypeScript 7.0.2 and happy-dom 21.0.4 from npm, on GitHub's Windows, macOS and Linux runners on x86-64 and Arm, from a folder whose name had accented letters. Each archive came in 0.1 to 1.2 seconds; `npm ci` took 1.4 to 29.9 seconds, the longest on Windows on Arm; tsc took 0.1 to 1.0 seconds, refused a wrong type with TS2322 everywhere; and `node --test` ran a test of a DOM in happy-dom in 0.3 to 1.3 seconds, with the same results on all six and no warnings.

## Why

The runner already fetches and pins what pip can't install, pgvector and llama.cpp's server, so Node joins them with the same checks and the same cache folder, and the learner still installs only uv. Node's own builds are the current security release on every system, where the wheels on PyPI lag it or miss a system. Node's test runner comes with Node, and its events are the interface its documentation offers to programs. Checking types before the tests keeps a stage from passing on code that doesn't compile, since Node strips types without checking them. The strongest case against: the runner now carries a second language's toolchain, whose pins move by hand, and a learner whose first TypeScript run is offline can't run it.

## Consequences

A learner's first TypeScript run fetches 31 to 54 MB of Node, and the lab's packages from registry.npmjs.org, and later runs, in any lab with the same lock, use the copies in the cache folder. A lab's TypeScript uses only syntax that can be erased, with no enums or parameter properties, and its tests import its files through `#`. A run's tests in one file share a process, and each file has its own. The lab's page says what the first run downloads and from where, and the Privacy Policy names nodejs.org and registry.npmjs.org. The page shows a TypeScript stage's solution in the editor, which highlights Python only, until the editor gains TypeScript.

## Revisit when

Node 24 leaves maintenance, a lab needs a browser rather than a DOM in Node, or Pyodide's browser runs can run TypeScript too.
