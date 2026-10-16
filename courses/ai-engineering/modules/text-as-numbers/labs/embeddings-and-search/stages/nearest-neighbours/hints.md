`np.argsort` sorts from the smallest up, so sort the negated similarities, along `axis=1`, and keep the first `k` columns.

---

`kind="stable"` keeps tied values in the order they come.
