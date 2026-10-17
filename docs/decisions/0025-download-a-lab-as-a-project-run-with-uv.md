# 25. Download a lab as a project the learner runs with uv

- Status: accepted
- Date: 2026-10-17

## Context

The Beginner capstone ends in a web service that runs on the learner's machine, not in the browser, and is called there. Record 17 runs code outside the browser through the `sulba` command, which isn't built: its distribution, and its tests on clean Windows, macOS and Linux machines, come first. The service needs only Python packages: the ones Pyodide ships, and a server. The learner's code is in browser storage. Module 1 has already taught `pyproject.toml`, `uv.lock` and `uv run`. The capstone's extract is 1.9 MB of CSV.

## Decision

- **Projects:** a lab whose code runs on the learner's machine has a `project/` folder: `README.md`, which says how to run it, `pyproject.toml`, `uv.lock` and, if its tests need one, `conftest.py`.
- **The download:** the lab's workspace has a Download button. It makes one zip in the browser: the project's files, the lab's data and the learner's files, as the open stage's run has them, without tests or checks, in a folder named for the lab. fflate makes the zip, loaded only when the learner downloads.
- **Versions:** a project pins what the browser runs: Python at Pyodide's version, and each package Pyodide ships at the version Pyodide ships. `pnpm check:content` holds each lock to that, to every package the lab's stages load, and to `uv lock --check`.
- **Serving:** the site serves a project's files as it serves datasets, at `/project/<hash>/<file>`, cached for good, and the workspace fetches them only for a download.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A zip made in the browser with fflate, run with uv (chosen) | Needs only uv, which Module 1 teaches; the learner's code goes from their browser to their machine; standard, compressed zips | Changes the learner makes on their machine don't come back to the browser |
| The same zip with client-zip | 2.6 kB gzipped; streams | Doesn't compress, and marks every zip as needing ZIP 4.5, which not every ZIP reader opens |
| The same zip with JSZip | Widely used | Four dependencies, and a dual licence |
| The `sulba` command (record 17) | One tool for every lab that runs locally | Not built; it would come first, for one lab's server |
| A GitHub repository template | Version control from the start | Every learner needs a GitHub account, and the site would link to a repository |
| Copying each file out of the editor | Nothing to build | Several files and a 1.9 MB extract by hand, with nothing to pin the packages |

## Evidence

- fflate's [README](https://github.com/101arrowz/fflate): "High performance (de)compression in an 8kB package", with ZIP archiving "for an extra 3 kB", synchronous `zipSync` and `unzipSync`, and typed arrays as its only browser requirement. MIT, version 0.8.3, no dependencies on npm.
- client-zip's [README](https://github.com/Touffy/client-zip): it "does *not* compress the files"; it is "6.4 kB minified, 2.6 kB gzipped"; it "will always specify 'ZIP version 4.5 required to unzip', even when that's not really true. The resulting files are not readable by every ZIP reader out there."
- JSZip 3.10.2 on npm depends on lie, pako, setimmediate and readable-stream, under "(MIT OR GPL-3.0-or-later)".
- MDN's [`<a>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/a): `download` "only works for same-origin URLs, same-origin `blob:`, and `data:` schemes". MDN's [`URL.createObjectURL()`](https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static) has been available across browsers since July 2015: "To release an object URL, call `revokeObjectURL()`."
- uv's [Python versions](https://docs.astral.sh/uv/concepts/python-versions/): "uv will automatically download Python versions if they cannot be found on the system."
- uv's [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/): when `uv run` is used, "the project is locked and synced before invoking the requested command"; `uv lock --check` is "equivalent to the `--locked` flag", with which "uv will raise an error instead of updating the lockfile" if it isn't up to date. Its [Project structure and files](https://docs.astral.sh/uv/concepts/projects/layout/) calls `uv.lock` "a universal or cross-platform lockfile" that "should be checked into version control, allowing for consistent and reproducible installations across machines".
- FastAPI's [FastAPI CLI](https://fastapi.tiangolo.com/fastapi-cli/): `fastapi dev` serves an app and reloads it on changes, `fastapi run` serves it for production, and "Internally, FastAPI CLI uses Uvicorn".
- Locally, `uv lock --check` on the fixture course's project answers from its lock without the network when the lock is current, and fails when `pyproject.toml` has changed since.

## Why

Every package the service needs is a Python package, so uv sets up the locked environment that record 17 planned for the `sulba` command, on any laptop, with a tool the course has already taught. A zip made in the browser keeps the learner's code between their browser and their machine. fflate writes standard compressed zips with no dependencies, and its `unzipSync` lets the tests read a download back. The strongest case against: the trip goes one way, so what the learner changes on their machine never reaches the browser or its tests.

## Consequences

A lab with a project has a Download in its workspace. A project's lock moves with Pyodide, as `packages/lab/python` does, so Renovate leaves it alone and a Pyodide upgrade relocks every project. The learner needs uv, and a network connection the first time `uv run` installs the project. The `sulba` command, its distribution and its tests on clean machines arrive with the first lab that needs more than Python packages.

## Revisit when

A lab needs what uv can't install, such as a GPU build or a local model server, or what the learner changes on their machine needs to come back to the browser.
