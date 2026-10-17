`-a` is `a * -1`, `a - b` is `a + -b`, and `a / b` is `a * b**-1`. With a number on the left, `__rsub__` and `__rtruediv__` get it as `other`: `other + -self` and `other * self**-1`.

---

`__pow__` records one step: `out = Value(self.data**exponent, (self,))`, whose `_backward` adds `exponent * self.data ** (exponent - 1) * out.grad` to `self.grad`.

---

`log`'s `_backward` adds `out.grad / a.data` to `a.grad`. `tanh`'s takes its derivative from the output it already has, `1 - out.data**2`.

---

`relu`'s output is `max(a.data, 0.0)`, and its `_backward` adds `(a.data > 0) * out.grad`, which is 0 at 0.
