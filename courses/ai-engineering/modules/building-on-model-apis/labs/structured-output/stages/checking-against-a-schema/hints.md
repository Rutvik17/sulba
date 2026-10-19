Check each keyword the schema has in turn, and for `properties`, `additionalProperties` and `items`, call `errors` on the value inside with its schema and its path, adding what it finds to your list.

---

In Python, `True` is an `int` and `True == 1`, so check for `bool` before `int`, both for `type` and for equality. `3.0.is_integer()` is true.

---

`additionalProperties` counts the keys that aren't in `properties`, and `len` counts a string's characters: `len("é")` is 1 when it's one character and 2 when it's an `e` with an accent after it.
