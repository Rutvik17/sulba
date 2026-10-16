# 22. Type-check a stage's code with mypy, in Pyodide and CPython alike

- Status: accepted
- Date: 2026-10-16

## Context

Python for programmers teaches type hints, so a stage's tests have to type-check the learner's code: ask whether a file passes `--strict`, and read each error it gets. The check runs wherever a stage runs, in Pyodide in the browser and in CPython on a learner's machine and in CI (decision record 17). It has to give the same errors in each, and leave a browser run's time limit to the learner's own code.

## Decision

- **The checker:** mypy 1.19.1, the version Pyodide 314.0.7 builds, called through `mypy.api.run` with `--strict`, no config file, and `--platform linux`, so a file gets the same errors in either runtime and on any machine.
- **Its wheels:** Pyodide's lock file lists only librt among mypy's dependencies. mypy 1.19.1 also requires typing_extensions, which Pyodide ships, and mypy_extensions and pathspec, which it doesn't. The site serves mypy_extensions 1.1.0 and pathspec 1.1.1 beside Pyodide's wheels, downloaded once from PyPI and checked against the sha256 PyPI gives, and the lock file it serves lists all three as mypy's dependencies. `packages/lab/python/uv.lock` pins the same versions for CPython, and a test fails when they differ.
- **In a test:** the runner's `typecheck` fixture gives mypy's errors in the session's files, one line each, as mypy prints them.
- **Its time:** mypy's cache stays in a folder for as long as the runner runs. Before a run that loads mypy starts its time, the runner checks the session's own files once, so the run's checks read the standard library's types from the cache.
- **What it leaves:** mypy raises Python's recursion limit and the garbage collector's thresholds, and keeps the types it has read for as long as Python runs. After each check the runner puts the limit and the thresholds back, and after the first it freezes what's left, so later garbage collections pass it over.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| mypy in Pyodide, with two wheels from PyPI (chosen) | The same version and errors in the browser and in CPython; Pyodide builds it, and its wheel is 6.6 MB | The site serves two wheels Pyodide doesn't ship; the first check in a browser takes seconds, so the runner does it before a run's time starts |
| Pyright | A type checker many editors use | No browser build: the Pyright Playground runs it on a server, which Sulba doesn't run (decision record 17) |
| ty | Fast, and from the makers of Ruff, which the editor already runs | In beta, and Astral publishes no browser build (decision record 14) |
| Type checks on the learner's machine, through the `sulba` command | Any checker, at full speed | The lab would leave the browser for a check the browser can run |

## Evidence

- Pyodide 314.0.7's lock file lists mypy 1.19.1 with librt as its only dependency, and typing-extensions 4.15.0 as a package of its own. It has no mypy-extensions or pathspec ([pyodide-lock.json](https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide-lock.json)). The mypy wheel is 6,589,936 bytes.
- mypy 1.19.1 requires typing_extensions 4.6.0 or later, mypy_extensions 1.0.0 or later, pathspec 0.9.0 or later and librt 0.6.2 or later ([PyPI](https://pypi.org/project/mypy/1.19.1/)). [mypy_extensions 1.1.0](https://pypi.org/project/mypy-extensions/1.1.0/) and [pathspec 1.1.1](https://pypi.org/project/pathspec/1.1.1/) are pure-Python wheels of 4,963 and 57,328 bytes.
- `mypy.api.run` takes a list of command-line arguments and returns mypy's standard output, its standard error and its exit status ([Extending and integrating mypy](https://github.com/python/mypy/blob/v1.19.1/docs/source/extending_mypy.rst)). `--platform` checks code as if it ran under another operating system, `--config-file=` with no file name ignores every config file, and `--cache-dir` sets where mypy keeps its cache ([The mypy command line](https://github.com/python/mypy/blob/v1.19.1/docs/source/command_line.rst)).
- Run through the runner, in Pyodide 314.0.7 under Node, the first check took 3.6 seconds and each later one 40 to 55 milliseconds. In CPython 3.14.2 a run with three checks took 2.9 seconds the first time, importing mypy included, and 0.65 seconds the next. `packages/lab/fixtures/uses-mypy` gives the same errors in both.
- mypy keeps a file's errors in its cache and gives them again while the file is unchanged, with the path it was first checked under: files checked first by their full path gave a later run that path. So the runner checks them first from their folder, by name, as a test does.
- mypy's `main` sets the recursion limit to 16,384, and `build` raises the garbage collector's thresholds to 200,000, 30 and 30 when Python is CPython, which Pyodide's is ([main.py](https://github.com/python/mypy/blob/v1.19.1/mypy/main.py), [build.py](https://github.com/python/mypy/blob/v1.19.1/mypy/build.py)). Neither puts them back. In Pyodide, a first check left about 152,000 more objects alive after a full collection, and a full collection took 247 milliseconds where it had taken 119. A run of a fixture without mypy took 1.15 seconds before any check and 1.75 seconds after one; with the leftovers frozen, along with everything loaded before them, it took 0.25 to 0.32 seconds.
- The [Pyright Playground](https://github.com/erictraut/pyright-playground)'s client "talks to the remote language server via an LSP session", and its server runs with `node index.js` (`client/LspClient.ts`, `server/README.md`).
- ty 0.0.89 is marked "Development Status :: 4 - Beta" on [PyPI](https://pypi.org/project/ty/). npm has no WebAssembly build of ty from Astral, where it has Ruff's ([@astral-sh/ruff-wasm-web](https://www.npmjs.com/package/@astral-sh/ruff-wasm-web)), as of 16 October 2026.

## Why

mypy is the only one of the checkers that runs in the browser today, and Pyodide already builds it at a pinned version that CPython can match. Two small pure-Python wheels, pinned by their hashes, are all it lacks. The strongest case against: the site now serves files Pyodide's release doesn't vouch for, and mypy's first check costs a few seconds in the browser, before the run starts.

## Consequences

A stage that loads mypy asks the learner's browser for 6.6 MB of wheels once, and spends a few seconds on its first check before its first run's time starts. Every check after that reads the cache. When Pyodide adds mypy's missing dependencies, or a mypy upgrade changes them, `packages/lab/src/assemble.ts` changes with it.

## Revisit when

Pyodide's lock file lists all of mypy's dependencies, or a faster checker publishes a browser build.
