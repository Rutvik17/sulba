`X @ w` multiplies each row of `X` by the weights and adds them up, one score per row. Add `b`, then pass the scores through `sigmoid`.

---

`np.exp(-z)` overflows when `z` is very negative. For those entries, use `np.exp(z) / (1 + np.exp(z))`, which is the same number.

---

Turn `z` into an array with `np.asarray(z, dtype=float)`, make the mask `z >= 0`, and fill the two parts of the result separately.
