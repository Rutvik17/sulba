# 49. Write specs in Markdown, edited in CodeMirror, with criteria numbered for tests to name

- Status: accepted
- Date: 2026-10-28

## Context

A spec says what a team wants built, and its acceptance criteria say when it's done (decision record 46). People write specs in the app, agents will read and write them through MCP, and the team's tests will prove each criterion by naming it. So a spec's text has to survive being written by a person and an agent in turn, and each criterion needs a name a test can carry that never changes its meaning. The app is React drawn in the browser (decision record 47), and its rows live in workspace tables guarded by row-level security, with every change logged (decision record 48).

## Decision

- **Tables:** `specs` holds each spec's title, status (draft, in review, approved, implemented, abandoned or superseded), owner and its text, and `criteria` holds each acceptance criterion's wording. A spec isn't deleted: it's abandoned or superseded, and keeps its number and history.
- **IDs:** a spec has a number in its workspace, SPEC-12, and a criterion a number in its spec, SPEC-12/AC-3. `create_spec` and `add_criterion` give them from counters that only go up, so a removed criterion's number is never given again. A test claims a criterion by putting its ID in the test's name. As names can't always hold a slash or a hyphen, the ID's parts may be joined by a hyphen, an underscore, a slash or a space, in any case: `test_SPEC_12_AC_3_retries` names SPEC-12/AC-3.
- **Text:** a spec's text is Markdown, stored as written, up to 50,000 characters. The app edits it in CodeMirror 6 with `@codemirror/lang-markdown` (`packages/editor/src/Markdown.tsx`), which keeps the Markdown marks in view, quietly, and saves a moment after the writer stops typing. The spec's page and its editor load only when a spec is opened.
- **History:** the log keeps each change to a spec and its criteria, with each event carrying its spec, so a spec's page reads its history in one request. The text is left out of the log, which records that it changed. Edits of the text alone by the same person within 10 minutes count as one change. An update that changes nothing isn't logged.
- **Who:** everyone in a workspace reads its specs; members and above write and change them, and a spec's owner is one of the workspace's members. Someone who leaves stops owning their specs.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Markdown stored as written, edited in CodeMirror 6 (chosen) | The text is exactly what a person or an agent wrote, so it diffs cleanly and round-trips through an agent; CodeMirror is already Sulba's editor, accessible by its own account, and Markdown adds about 38 KB compressed to it | People see Markdown's marks rather than formatted text |
| Tiptap, storing its own JSON or Markdown through `@tiptap/markdown` | A familiar rich-text editor, MIT at its core | Its Markdown extension is in beta, 146 KB compressed, and text an agent writes would be re-serialised when a person edits it |
| BlockNote | Blocks like Notion's out of the box | 403 KB compressed, export features GPL or paid, its own UI kit, and Markdown that its docs call lossy |
| Lexical, ProseMirror or Milkdown | Mature editing cores | Each stores its own document format and leaves Markdown to a converter, and two need their whole interface built |
| Criteria inside the Markdown, as a list | One field to edit | A criterion would lose its number when the list was edited, so a test's name would stop meaning one thing |
| IDs from row ids | Nothing to count | Unreadable in a test's name, a branch or a commit |

## Evidence

- Bundle sizes measured on 2026-10-27 for the same features in each editor, minified and compressed with gzip -9, React external: CodeMirror's Markdown on top of what Sulba's editor already loads 38 KB, Lexical 97 KB, ProseMirror 132 KB, Milkdown 139 KB, Tiptap 146 KB, Plate 303 KB, BlockNote 403 KB.
- [Tiptap, Markdown](https://tiptap.dev/docs/editor/markdown): `@tiptap/markdown` is marked beta, an early release with known limits.
- [Tiptap, Accessibility](https://tiptap.dev/docs/guides/accessibility): a headless editor leaves the interface's accessibility to the app.
- [BlockNote, Markdown import](https://www.blocknotejs.org/docs/features/import/markdown) and [export](https://www.blocknotejs.org/docs/features/export/markdown): both lossy; and [BlockNote's pricing](https://www.blocknotejs.org/pricing) for its XL features.
- [Lexical, Introduction](https://lexical.dev/docs/intro) and [@lexical/markdown](https://lexical.dev/docs/packages/lexical-markdown): its own editor state, with Markdown through transformers.
- [CodeMirror](https://codemirror.net/): works with screen readers and keyboard-only use; `@codemirror/lang-markdown` 6.5.2, published August 4, 2026.
- Measured on this repository: the spec page's script, with the editor, is 180 kB compressed and loads when a spec opens; the app's first script is 178 kB. `packages/data/supabase/tests/specs.test.sql` runs 37 pgTAP tests, among them that visitors can't call its functions, that a removed criterion's number isn't given again, that two saves of a spec's text log one change without the text, and that a viewer changes nothing.

## Why

Specs are written by people and agents in turn, and Markdown is the form both write without conversion, so storing it as written means neither one's edit reformats the other's. CodeMirror edits that text as it is, is already in Sulba's stack and tests, and costs least. Criteria live in their own rows so each keeps its number whatever happens to the text around it, and numbers that only go up make an ID in a test's name mean one criterion forever.

The strongest case against it is that many people expect a document editor to show formatted text. Markdown's marks stay visible, quietly, and a rich-text editor can be added later over the same stored Markdown once one keeps it as written.

## Consequences

- Evidence will match test names to criteria by the rule above, and the app shows that rule where criteria are written.
- A spec's text keeps no versions yet: the history says when it changed and who changed it, not what it said before.
- Two people editing a spec's text at once each save their own, and the last save wins, until live editing arrives.

## Revisit when

Teams ask for formatted editing, two people often edit one spec at once, or the history needs a spec's earlier text.
