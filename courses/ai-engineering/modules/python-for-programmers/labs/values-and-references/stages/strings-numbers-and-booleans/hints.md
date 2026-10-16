`bool` is a subclass of `int`, so `isinstance(True, int)` is `True`. In JavaScript, `typeof true` is `'boolean'`: rule booleans out first.

---

`math.isnan(value)` says whether a float is NaN. It turns an int into a float first, which fails for an int too large for a float, so ask it only about floats.

---

`value.is_integer()` says whether a float has no fraction. It's false for infinity and NaN, as `Number.isInteger` is.
