In training, `mean, var = X.mean(axis=0), X.var(axis=0)`: NumPy's `var` divides by `n`, the batch's own variance. The unbiased one for the running estimate is `var * n / (n - 1)`.

---

Keep what the backward pass needs from the forward: `self.scale = 1 / np.sqrt(var + self.eps)` and the normalized batch, `(X - mean) * self.scale`.

---

The backward pass is the brief's formula with `axis=0` sums: `dnormalized = dY * self.weight`, then `self.scale / n * (n * dnormalized - dnormalized.sum(axis=0) - normalized * (dnormalized * normalized).sum(axis=0))`.
