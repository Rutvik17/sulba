Each entry of a matrix product is a dot product of a row of the first matrix with a column of the second, and the columns of `B.T` are the rows of `B`:

```math
(A B^\top)_{ij} = \sum_{k=1}^{d} A_{ik} B_{jk}
```

| Symbol | Meaning |
| --- | --- |
| `$A_{ik}$` | Measurement `$k$` of new sample `$i$` |
| `$B_{jk}$` | Measurement `$k$` of record `$j$` |
| `$d$` | The number of measurements, {% $fig.measurements %} |

For the {% $fig.new %} new samples against the {% $fig.records %} records, that is {% $fig.multiplications %} multiplications, as many as broadcasting's subtractions, but they are added up as they go: the result holds {% $fig.pairs %} numbers, {% $fig.result_mb %} MB, where the differences took {% $fig.broadcast_mb %} MB. The squared lengths are one number a row, and a search that keeps its records can work theirs out once. scikit-learn's `euclidean_distances` works distances out this way too, for speed, and so that one side's squared lengths can be worked out once and kept.

The identity holds exactly for real numbers, but floats are rounded. NumPy's arrays here hold float64 numbers, which keep about {% $fig.digits %} significant decimal digits, and the squared lengths can be far larger than the squared distance between them. Subtracting nearly equal numbers then leaves mostly rounding, which is called catastrophic cancellation.

Take two samples {% $fig.gap %} apart in one measurement, at {% $fig.far %} and {% $fig.far_plus %}. The square of {% $fig.far_plus %} is {% $fig.far_plus_squared %}, an odd number, and float64 numbers near `$10^{16}$` are {% $fig.spacing %} apart, so it is kept as {% $fig.stored %}. The squared distance comes out {% $fig.far_squared %} instead of {% $fig.gap_squared %}, a distance of {% $fig.far_distance %}. Two samples {% $fig.gap %} apart at {% $fig.further %} come out {% $fig.further_distance %} apart. The chart shows your `fast_distances` for two such samples as they sit further from 0.

Rounding can also take a squared distance below 0, where its square root is `nan`: for samples at {% $fig.low %} and {% $fig.high %}, it comes out {% $fig.below %} where it should be {% $fig.true_below %}. Counting it as 0 keeps every distance a number, though not the right one.

Standardized measurements sit around 0, where squared lengths stay small. On the clinic's standardized samples, the fast distances agree with `cdist`'s to within 1 part in `$10^{\fig{bound}}$`.
