`re.findall(r"\[(\d+)\]", reply)` gives the numbers a reply cites, as strings, in order. Number `n` names the passage at place `n - 1`.

---

Read the passages' titles and texts in one query, `SELECT id, title, body FROM passages WHERE id = ANY(%s)`, given the list of ids `find` gave, and number them in `find`'s order.

---

`httpx.HTTPError` covers an error status, a dropped connection and a timeout. A reply whose JSON lacks what you read raises `KeyError` or `IndexError`, and a body that isn't JSON a `ValueError`.
