`unbroadcast` first sums away the axes broadcasting added in front, `while grad.ndim > len(shape): grad = grad.sum(axis=0)`, then sums along each axis that has length 1 in `shape` but not in `grad`, with `keepdims=True`.

---

`__add__` adds `unbroadcast(out.grad, self.data.shape)` to `self.grad`, and the same for `other`. `__mul__` multiplies by the other tensor's data first: `unbroadcast(other.data * out.grad, self.data.shape)`.

---

The matrix product's gradients are the linear layer's: `out.grad @ other.data.T` for `self`, and `self.data.T @ out.grad` for `other`.

---

`sum`'s backward spreads `out.grad` back over the axis it summed: `np.expand_dims(grad, axis)` puts the axis back when `keepdims` was False, and `np.broadcast_to(grad, self.data.shape)` stretches it. `mean` is `sum` times one over the number of elements it averaged.
