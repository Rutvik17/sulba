Call `check` first, and give its message when it has one, before `test` runs.

---

`result is True` holds for `True` alone. `if result:` would pass any value that's true, such as a number or a match.

---

`refined.__name__ = check.__name__` gives the new check its check's type.
