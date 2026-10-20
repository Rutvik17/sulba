`vectors.mean(axis=1, keepdims=True)` gives each row's mean as a column, which NumPy takes away from every number of its row.

---

`np.linalg.norm(kept, axis=1, keepdims=True)` gives each row's length, to divide the row by.

---

`np.round`, then `np.clip(steps, 0, 255)`, then `.astype(np.uint8)`: a value past 255 that reaches `astype` uncut has no defined result.
