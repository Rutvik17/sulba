`self.test(value)` calls the method of the instance's own class, so `Struct.failures` tests a number as `Number` does.

---

`value.get(key, MISSING)` gives `MISSING` for a field the value leaves out.

---

`Type.entries` can take each entry from `super().entries(value)` and keep those whose key is in the schema.
