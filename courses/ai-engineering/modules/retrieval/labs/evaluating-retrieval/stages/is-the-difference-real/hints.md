Swapping a question's two values turns its difference `a - b` round. Multiply the differences by `1 - 2 * draws`, a row a resample, and take the mean of each row.

---

`a[rows]` holds a resample of `a` in each row, and `b[rows]` the same questions of `b`.

---

`np.quantile(differences, [(1 - confidence) / 2, (1 + confidence) / 2])` gives both ends at once.
