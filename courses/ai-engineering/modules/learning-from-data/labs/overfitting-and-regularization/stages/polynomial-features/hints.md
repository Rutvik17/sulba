`combinations_with_replacement(range(X.shape[1]), size)` gives each set of `size` column numbers, a column allowed more than once, in order: `(0, 0)`, `(0, 1)`, and so on.

---

`np.prod(X[:, list(columns)], axis=1)` multiplies those columns together, one product per row.

---

Make the products for each size from 1 to `degree` in turn, then put them side by side with `np.column_stack`.

---

`np.sqrt(np.mean((y - y_hat) ** 2))` is the root mean squared error, and `float` turns NumPy's number into Python's.
