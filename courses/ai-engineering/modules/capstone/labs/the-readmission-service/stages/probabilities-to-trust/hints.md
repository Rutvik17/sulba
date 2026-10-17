Start from `np.empty(len(table))`, and for each fold put its probabilities at the held-out positions: `probabilities[test] = scores(make_model(), table.iloc[learn], table.iloc[test])`.

---

`np.bincount(group, weights=p, minlength=bins)` adds up each group's probabilities, and `np.bincount(group, minlength=bins)` counts its stays. Divide the one by the other where the count isn't 0.

---

Turn `y` and the probabilities into float arrays with `np.asarray(..., dtype=float)` before you subtract.
