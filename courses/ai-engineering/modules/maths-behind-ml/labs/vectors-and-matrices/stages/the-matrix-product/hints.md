`B.T` turns the rows of `B` into columns, so `A @ B.T` takes each row of `A` with each row of `B`.

---

`np.sum(A**2, axis=1)` gives each row's squared length. Make one a column with `[:, None]` and the other a row with `[None, :]`, so that adding them gives the shape (len(A), len(B)). `np.maximum(squared, 0)` replaces anything below 0 with 0.
