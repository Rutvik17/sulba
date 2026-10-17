Turn the probabilities into an array with `np.asarray(probabilities, dtype=float)`, so a list works too, and take `np.quantile(..., 1 - share)` of it.

---

`called = probabilities >= threshold` is True for each stay called. With `y` as booleans, `np.asarray(y, dtype=bool)`, the readmissions among them are `called & y`.

---

Recall divides the readmissions called by all the readmissions, and precision divides them by the stays called. Return the count as an `int`.
