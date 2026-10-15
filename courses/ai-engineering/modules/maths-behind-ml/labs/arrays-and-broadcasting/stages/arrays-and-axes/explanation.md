An array has a shape. The records' measurements have the shape ({% $fig.records %}, {% $fig.measurements %}): {% $fig.records %} rows along axis 0, one per sample, and {% $fig.measurements %} columns along axis 1, one per measurement. A reduction collapses the axis it's given. `np.mean(X, axis=0)` averages down each column and leaves one number per measurement, while `axis=1` would average across each row and leave one number per sample.

The standard deviation `StandardScaler` uses divides by the number of rows:

```math
\sigma_j = \sqrt{\frac{1}{n} \sum_{i=1}^{n} \left(x_{ij} - \mu_j\right)^2}
```

| Symbol | Meaning |
| --- | --- |
| `$x_{ij}$` | Measurement `$j$` of record `$i$` |
| `$\mu_j$` | The mean of measurement `$j$` over the records |
| `$n$` | The number of records, {% $fig.records %} |

That is NumPy's default. `np.std(X, axis=0, ddof=1)` divides by `$n - 1$`, {% $fig.n_minus_one %}, instead, which makes every standard deviation here {% $fig.ddof_larger %} larger. Either is a fair measure of spread, but numbers made with one don't match numbers made with the other.

Indexing with a mask is advanced indexing, and advanced indexing always copies: `table[~new, 2:]` is a new array. A slice such as `table[:, 2:]` is a view of the table's own memory, so writing into the slice writes into the table. Code that changes an array it was given, in place, changes it for everyone who holds it.

The measurements are on very different scales. Among the records, the smallest standard deviation is the {% $fig.low_name %}'s, {% $fig.low_std %}, and the largest is the {% $fig.high_name %}'s, {% $fig.high_std %}: {% $fig.ratio %} times as large. A distance between samples worked out from these raw numbers would be decided by the largest of them, and the next stage puts every measurement on the same scale.
