`isinstance(other, Union)` tells a union from any other struct, so `__or__` can take a union's members, or the struct itself as a tuple of one.

---

`list(member.failures(value, path))` is empty for a member the value passes, so `all(found)` is true only when every member has failed.

---

`{self.schema!r}` in an f-string shows the dict with `repr`, which shows each struct in it with its own `__repr__`.
