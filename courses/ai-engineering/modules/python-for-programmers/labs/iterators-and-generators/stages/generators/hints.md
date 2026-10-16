`(*path, key)` is a new tuple: `path` with `key` added at the end.

---

`yield from failures(value[key], field, (*path, key))` yields every failure inside the field, with the field's path.

---

After a value fails as a whole, `return` ends the generator, so nothing inside the value is checked.
