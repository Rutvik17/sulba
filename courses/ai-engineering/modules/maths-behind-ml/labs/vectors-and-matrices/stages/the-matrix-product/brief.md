Broadcasting works out the distances from {% $fig.new %} new samples to {% $fig.records %} records through an array of every difference, {% $fig.multiplications %} numbers. A squared distance needs only dot products, since `$\lVert a - b \rVert^2 = a \cdot a + b \cdot b - 2\, a \cdot b$`, and every dot product between two sets of samples comes from one matrix product.

`A @ B.T` multiplies `A`, of shape (m, d), by `B.T`, of shape (d, n). The result has the shape (m, n), and its entry in row `i` and column `j` is the dot product of row `i` of `A` with row `j` of `B`.

Write `pairwise_dots`, every dot product at once. Then write `fast_distances`, each distance from those dot products and the rows' squared lengths, with no array of differences. Rounding can take a squared distance a little below 0 where it should be 0 or close to it, and its square root would be `nan`, so count one below 0 as 0.

```
pairwise_dots(A, B) -> an array of shape (len(A), len(B))
fast_distances(A, B) -> an array of shape (len(A), len(B))
```

The tests compare `pairwise_dots` with `np.dot`, and `fast_distances` with SciPy's `cdist`.
