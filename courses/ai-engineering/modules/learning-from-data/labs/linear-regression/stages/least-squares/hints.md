Add a column of ones to `X`, so the bias becomes one more weight: `np.column_stack([X, np.ones(len(X))])`.

---

`np.linalg.lstsq(A, y, rcond=None)` returns the least-squares solution first, then three other values you don't need.

---

The solution's last entry is the bias, and the entries before it are the weights.
