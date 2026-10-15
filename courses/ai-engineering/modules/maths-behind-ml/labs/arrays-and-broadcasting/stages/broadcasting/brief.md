Measurements on such different scales can't be compared as they are. Standardizing puts them on one footing: subtract the records' mean from each measurement, then divide by the records' standard deviation, so that over the records every measurement has a mean of 0 and a standard deviation of 1. A new sample is standardized with the records' mean and standard deviation, not its own: it may arrive alone, with no spread of its own to divide by.

NumPy does this for every row at once by broadcasting. With `X` of shape (n, {% $fig.measurements %}) and `mean` of shape ({% $fig.measurements %},), `X - mean` subtracts the mean from every row. NumPy lines the two shapes up from the right, and an axis that is missing, or has length 1, is stretched to match the other.

Write `standardize`, as `StandardScaler`'s `transform` does it. A column whose standard deviation is 0 is divided by 1, so it stays at 0 rather than becoming `nan`.

Then write `distances`, the Euclidean distance from each row of `A` to each row of `B`, without a Python loop. `A[:, None, :]` has the shape (m, 1, {% $fig.measurements %}) and `B[None, :, :]` the shape (1, n, {% $fig.measurements %}), so their difference has the shape (m, n, {% $fig.measurements %}): every row of `A` against every row of `B`.

```
standardize(X, mean, std) -> X, standardized
distances(A, B) -> an array of shape (len(A), len(B))
```

The tests compare `standardize` with scikit-learn's `StandardScaler`, and `distances` with SciPy's `cdist`.
