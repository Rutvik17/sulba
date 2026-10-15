For each tree, a boolean array that starts all True, with `left_out[sample] = False`, marks the rows its sample left out.

---

Keep two running arrays: the sum of the shares each row got from the trees that left it out, and how many trees those were. A tree that left no row out has nothing to score.

---

`np.full(len(X), np.nan)` starts every row at NaN, and `np.divide(total, count, out=shares, where=count > 0)` fills in the rows with at least one tree.
