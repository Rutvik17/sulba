`table[:, 0]` is column 0, one number per row, and `table[:, 2:]` every column from 2 on. Make the mask once, `new = table[:, 0] == 1`, and use `~new` for the records.

---

`table[new, 2:]` takes the rows where the mask is `True` and the columns from 2 on, in one step.

---

`np.mean(X, axis=0)` averages down each column, giving one number per column. `np.std` takes the same `axis`, and divides by the number of rows unless it's told otherwise.
