With every distance in one array, a row per new sample and a column per record, the records nearest a sample are the columns of the smallest numbers in its row. `np.argsort` gives the positions that would sort an array, along the axis it's given: for a row of distances, the record numbers from nearest to farthest.

Write `nearest`, which returns the column numbers of the `k` smallest distances in each row of `D`, smallest first. Where two distances are equal, the column that comes first stays first, as a stable sort leaves them.

Then write `malignant_share`: for each row of `near`, the share of the records it names that are malignant. Indexing an array with an array of positions gives an array of the positions' shape, so `diagnoses[near]` has a row of diagnoses for each new sample.

```
nearest(D, k) -> an array of shape (len(D), k)
malignant_share(near, diagnoses) -> one share per row of near
```

The tests use your `standardize` and `distances`, and compare `nearest` with scikit-learn's `NearestNeighbors`.
