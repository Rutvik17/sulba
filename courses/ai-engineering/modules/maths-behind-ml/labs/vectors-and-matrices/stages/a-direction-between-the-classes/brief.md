The two class means give a direction: from the average benign record to the average malignant one. Every sample has a position along it, measured from the midpoint of the two means. That position is the sample's score: above 0, the sample is nearer the malignant mean, and below 0, nearer the benign one.

Write `direction`, the vector of length 1 that points from `mu0` to `mu1`.

Then write `scores`, each row's signed distance from the midpoint of `mu0` and `mu1` along that direction. The distance along a direction of length 1 is a dot product, and `Z @ u` takes the dot product of every row of `Z` with `u` at once.

```
direction(mu0, mu1) -> a vector of length 1
scores(Z, mu0, mu1) -> one score per row of Z
```

The tests score the {% $fig.new %} new samples, standardized with the records' mean and standard deviation, and compare the signs with scikit-learn's `NearestCentroid`, which puts each sample with the class whose mean is nearer.
