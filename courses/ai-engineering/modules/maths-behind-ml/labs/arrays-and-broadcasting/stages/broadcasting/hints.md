`np.where(std == 0, 1, std)` is `std` with each 0 replaced by 1. Dividing by it leaves every other column as it was.

---

Subtract first, with `A[:, None, :] - B[None, :, :]`, and check the result's shape. Squaring keeps it; `np.sum(..., axis=-1)` adds up the last axis, the measurements, and leaves the shape (m, n).

---

`np.sqrt` of those sums is the distance. Nothing in either function needs to change the arrays it's given: `X - mean` makes a new array.
