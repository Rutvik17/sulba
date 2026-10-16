Inside `literal`, a `def check(value):` can use `constant`, and `return check` returns the function itself, not a call to it.

---

A closure keeps a reference to the list it was given, as any variable does. `tuple(options)` makes a copy that nothing outside holds.

---

`check.__name__` is the name the function was defined with, such as `'number'`.
