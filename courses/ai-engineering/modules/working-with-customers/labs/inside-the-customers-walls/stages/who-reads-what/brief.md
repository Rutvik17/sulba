The office liked the pilot, and wants the desk for its own staff too: a search of its staff guidance, which isn't for every member of staff. It holds its documents in `access.py`'s `DOCUMENTS`, each a `Document` naming the groups that may read it: `benefits`, `veterans`, `front-desk` and `supervisors`. A document that names no group, such as a draft, is for no one yet.

In `access.py`, write:

- `readable(documents, groups)`: the documents someone in `groups` may read, in their order: those that name one of the groups.
- `search(question, documents, groups, k=3)`: of the documents someone in `groups` may read, the `k` that share the most words with the question, among those that share any, the earlier first where two share as many. Words are compared in lower case, without punctuation, and a word of fewer than four letters doesn't count; a document's words are those of its title and its text.

```
readable(documents, groups) -> list[Document]
search(question, documents, groups, k=3) -> list[Document]
```
