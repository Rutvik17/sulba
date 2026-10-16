Rule booleans out first again: `True == 1` in Python, where `true === 1` is false in JavaScript.

---

For lists and dicts, `a is b` is JavaScript's `===`: two equal lists are still two lists.

---

NaN is never `==` NaN, so `enums` needs a test of its own for it, with `math.isnan`.
