`define(name)` returns a function that takes the test and returns the check, so there are two `def`s inside it.

---

`@functools.wraps(test)` above the inner `def` copies `test`'s name and docstring onto it. Set `check.__name__ = name` after, for the type.

---

A function is an object, and can hold attributes of its own: `counting.failed = 0`, then `counting.failed += 1` inside it.
