`json.JSONDecodeError` is the error `json.loads` raises for text that isn't JSON. It's a kind of `ValueError`.

---

In `check_line`, catch the `StructError`, add the note, and `raise` it again, so the caller gets the same error with its failures.

---

`enumerate(lines, 1)` numbers the lines from 1. `check_day` catches `(StructError, ValueError)` for each line, and raises its group after the loop when it kept any.
