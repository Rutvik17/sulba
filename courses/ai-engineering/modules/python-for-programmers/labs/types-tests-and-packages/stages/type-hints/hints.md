A dataclass takes its fields from the annotations in its body: `path: tuple[str | int, ...]` and `message: str`, one a line.

---

In `check_number`, test `isinstance(value, bool)` first, since a bool is an int. After `not isinstance(value, int | float)` has ruled out everything else, mypy knows `value` is a number, and lets `math.isnan(value)` through.

---

`label` reads `sample.get("note")` and adds `f": {note}"` only when it isn't `None`.
