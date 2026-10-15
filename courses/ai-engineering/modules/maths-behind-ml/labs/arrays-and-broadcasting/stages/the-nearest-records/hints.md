`np.argsort(D, axis=1)` sorts each row on its own. Take the first `k` columns of its result with `[:, :k]`.

---

The default sort doesn't promise an order for equal values. `kind="stable"` keeps them in the order they came.

---

`diagnoses[near]` has the shape of `near`, and `np.mean(..., axis=1)` averages along each row.
