mypy checks code against its annotations, so read each one as a promise, and ask whether the code keeps it.

---

`cast` and `# type: ignore` both tell mypy to stop asking. Work out what it would have said.

---

Which numbers does an annotation of `float` take, and which does `isinstance(value, float)` take?
