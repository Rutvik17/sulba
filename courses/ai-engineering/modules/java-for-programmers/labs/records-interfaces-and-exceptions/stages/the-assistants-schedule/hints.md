Java's `==` on two objects asks whether they're the same object. Java keeps one object for each string literal, so two literals with the same text are always `==`.

---

`List<Integer>` has two `remove` methods: `remove(int index)` and `remove(Object o)`. With an `int`, Java picks the first.

---

A `HashMap` promises no order for its keys.
