`next(failures, None)` takes a generator's first value, or `None` when it has none, and leaves the rest in the generator for `StructError` to keep.

---

A generator can be read only once, so `failures()` builds its list the first time it's called and keeps it on the error.

---

`validate` can call `assert_` in a `try` clause, and return from its `except StructError as error:` clause and from an `else:` clause.
