Before your team took the work on, an assistant wrote the desk's search for staff, `staff_search.py`'s `search_for`: it reads the person's groups from their ID token, searches what they may read, and adds a line to the audit log. It maps the groups with your `GROUPS` and writes the log's `who` with your `pseudonym`. Its three tests all pass.

Review it as if the office's auditors were about to read its code: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the office will run it. A run shows how many pass. You see which ones when you finish the review.

What the search must do:

- take a person's groups only from a token that checks out;
- give the `k` best documents of those the person may read;
- give no one a document that names no group;
- keep to what the auditors need in the log.

```
search_for(keys, id_token, question, *, client_id, key, log, at,
           documents=DOCUMENTS, k=3) -> list[Document]
```
