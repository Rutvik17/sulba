# 14. Use CodeMirror 6, with each language's own browser build

- Status: accepted
- Date: 2026-10-11
- Supersedes: [6. Use CodeMirror 6 with language servers](0006-use-codemirror-with-language-servers.md)

## Context

Record 6 chose CodeMirror 6 and planned to give each language its features through `@codemirror/lsp-client`, with a language server compiled to WebAssembly in a Web Worker. For Python, the architecture plan named Ruff for errors and formatting and ty for types, completion and hover. Building the editor showed that neither speaks the Language Server Protocol in the browser. Ruff publishes a WebAssembly build with its own small API. ty publishes none: its playground compiles one from source.

## Decision

The editor stays CodeMirror 6, for the reasons in record 6. A language gets its features from its own official browser build, through that build's API, wherever one exists. For Python that is Ruff: it marks errors and likely mistakes as the learner types, and formats the code, in a Web Worker. Completion comes from CodeMirror's Python package: the names defined in the file, Python's built-ins and keywords. A language whose tooling only exists as a language server still goes through `@codemirror/lsp-client`.

## Options

| Option for Python | What it does well | Where it falls short |
| --- | --- | --- |
| Ruff's own browser build, through its API (chosen) | Published by Astral for every release. Catches syntax errors, undefined and unused names, and formats in the style learners meet at work | 10.9 MB, 2.6 MB compressed. No types, hover or completion |
| ty, compiled from Ruff's repository in CI | Types, completion with members, hover | Astral publishes no build, so CI would need Rust and wasm-pack at a pinned commit on every change. The only `ty_wasm` on npm is a third party's version 0.0.0 |
| jedi, running in a second Pyodide | Completion with members and signatures, docstrings on hover. Pyodide 314.0.7 ships jedi 0.19.2 | A second Python in the page: its files are already cached, but it doubles the memory, which phones have little of. The first can't serve it, because a test run blocks it for up to 5 seconds |
| A language server through `@codemirror/lsp-client` | One client for every language | No Python language server runs in the browser |

## Evidence

- Ruff's browser build: [`@astral-sh/ruff-wasm-web`](https://www.npmjs.com/package/@astral-sh/ruff-wasm-web), published under Ruff's MIT licence from [astral-sh/ruff](https://github.com/astral-sh/ruff). Its types expose `check`, `format`, `parse` and `tokens`, and no protocol messages. Version 0.16.10's WebAssembly file is 10,924,574 bytes, 3.8 MB with gzip and 2.6 MB with Brotli, measured on 11 October 2026.
- ty's playground builds it with `wasm-pack build ../../crates/ty_wasm` before bundling ([playground/ty/package.json](https://github.com/astral-sh/ruff/blob/main/playground/ty/package.json)).
- [`ty_wasm`](https://www.npmjs.com/package/ty_wasm) on npm is version 0.0.0, published on 26 May 2026 by an account outside Astral.
- jedi 0.19.2 and parso 0.8.6 are in [Pyodide 314.0.7's lock file](https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide-lock.json).
- [`@codemirror/lang-python`](https://github.com/codemirror/lang-python) 6.2.1 adds two completion sources: names defined in the file, and a list of built-ins, keywords and snippets.

## Why

Ruff gives learners the feedback that matters most while they type: a syntax error or a name Python can't find, marked before they run anything. It comes from the toolmaker, so every version is a pinned npm package with no compiler in CI. Completion with members and types is worth having, but each way to get it today costs a build pipeline or a second Python runtime.

The strongest case against: completion that knows NumPy's members helps beginners, and jedi offers it now.

## Consequences

The editor marks mistakes and formats, but it doesn't complete `np.` members or show types. Ruff's WebAssembly downloads once, after the page is usable, and is cached. Each language needs its own small adapter rather than one client for all.

## Revisit when

Astral publishes a browser build of ty, or learners ask for completion of library members. jedi in a second worker is the next option then.
