Moving every sample by the same vector `$c$` changes no difference between two samples, and so no distance:

```math
\lVert (a - c) - (b - c) \rVert = \lVert a - b \rVert
```

It does change the squared lengths, and moved by the records' mean, they stay about the size of the records' spread. With {% $fig.shift %} added to each of the {% $fig.measurements %} measurements, a sample's squared length is near `$\fig{lengths}$`, where float64 numbers are {% $fig.far_spacing %} apart, and {% $fig.share_below %} of the squared distances between the new samples and the records are smaller than that. `Nearest` moves its records by their mean once, when it's made, and each new sample by the same mean when it's looked up.

A sample's squared distance to its copy is `$a \cdot a + a \cdot a - 2\, a \cdot a$`. That is 0 only if `np.sum` and the matrix product round `$a \cdot a$` alike, and for many records they don't. Standardized, a record's squared length averages {% $fig.average_length %}, the number of measurements, so `$a \cdot a + a \cdot a$` is near {% $fig.twice %}, where one unit in the last place is `$\fig{ulp}$`. Its square root is `$\fig{ulp_root}$`: one unit off, and the copy is shown that far away. So `find` works out the distances of the `k` records it found again, from their differences. A sample less its copy is exactly 0, and the other distances come out as `cdist` gives them, for `$k \times d$` subtractions a sample, where the dot products took `$n \times d$` multiplications.

The dot products for {% $fig.lookups %} samples against {% $fig.big_records %} records hold {% $fig.matrix_mb %} MB, where the differences between them would hold {% $fig.full_mb %} MB, and their squares as much again.
