`__add__` makes a number a Value first, `other = other if isinstance(other, Value) else Value(other)`, then makes `out = Value(self.data + other.data, (self, other))` and gives it a `_backward` that adds `out.grad` to both their gradients. `__radd__` is `self + other`.

---

The derivative of `$a b$` with respect to `$a$` is `$b$`, so `__mul__`'s `_backward` adds `other.data * out.grad` to `self.grad`, and `self.data * out.grad` to `other.grad`. The derivative of `$e^a$` is `$e^a$` itself: `out.data * out.grad`. `np.exp` takes a single number too.

---

Use `+=`, never `=`. A value used twice, as in `a * a`, gets a gradient from each use, and the two add up.

---

`topological_order` can visit recursively: skip a value it has already seen, visit its parents, then append it. `backward` sets `self.grad = 1.0` and calls `_backward` on each value in `reversed(topological_order(self))`.
