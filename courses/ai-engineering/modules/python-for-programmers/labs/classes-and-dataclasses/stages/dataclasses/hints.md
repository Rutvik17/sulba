In a dataclass, `path: tuple` on a line of the class body is a field. A field with `= None` after it has a default, and must come after the fields without one.

---

Inside the class, `self.path` is the instance's path.

---

`self.path[-1]` is a tuple's last item, and an empty tuple is falsy.
