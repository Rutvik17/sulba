`dict(record)` is a new dict with the same fields. Change the new one, and `record` stays as it was.

---

`key not in record` is true only when the field is missing: a field set to `None`, `0` or `""` is in the dict.

---

`callable(default)` says whether `default()` can be called. `list` can: `list()` is a new, empty list.
