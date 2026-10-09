# 6. Use CodeMirror 6 with language servers

- Status: accepted
- Date: 2026-10-08

## Context

The workspace needs an editor with completion, errors as you type and formatting. It has to load quickly and work on phones.

## Decision

CodeMirror 6 with `@codemirror/lsp-client`. Each language server runs in a Web Worker and loads only for lessons in that language.

## Options

| | CodeMirror 6 (chosen) | Monaco (VS Code's editor) |
| --- | --- | --- |
| Size | 1.26 MB | 5.01 MB |
| Phones | Supported | Not supported |
| Language servers | Official client: completion, hover, signature hints, go to definition, rename, formatting, diagnostics | Built in, through VS Code's own protocol layer |
| Used by | Exercism (its website's dependencies, checked 8 October 2026), Replit | VS Code for the web, Ruff's and ty's playgrounds |

## Evidence

- Sizes and Replit's switch: [Replit](https://replit.com/blog/codemirror).
- Monaco's README answers "No" to mobile support ([Monaco](https://github.com/microsoft/monaco-editor)).
- The client's features are from its author's announcement ([CodeMirror forum](https://discuss.codemirror.net/t/codemirror-lsp-client/9309)).
- Exercism's dependencies: [exercism/website](https://github.com/exercism/website).

## Why

CodeMirror is a quarter of Monaco's size, it works on phones, and the same language servers that power Monaco's features plug into it.

## Consequences

Sulba wires up each language's server itself, and a large server such as clangd downloads slowly the first time. A language's server is added with the first session that uses it.

## Revisit when

A needed language has no server that runs in the browser. That language then gets compiler errors from the test run instead.
