Estimate the error of the whole procedure: choosing by cross-validation, then fitting.

The chosen pair's cross-validated RMSE is the lowest of {% $fig.pairs_tried %}, so it can't stand for the error on new mixes: the pair partly won by suiting those folds. Nested cross-validation measures the whole procedure instead. Deal the records into `k` outer folds with `folds`. In each, choose the degree and penalty on the outer fold's fit tests alone, by `k`-fold cross-validation over folds of their own mixes with the same seed. Then fit the chosen pair on those fit tests and measure its RMSE on the outer fold's held-out tests.

`nested` returns the mean of the outer folds' errors, and the pair each outer fold chose.

```
nested(X, y, mixes, degrees, penalties, k, seed) -> (rmse, [(degree, penalty), ...])
```

The inner folds come from `folds(mixes[fit], k, seed)`, so their row numbers count within the outer fold's fit tests, as `choose` gets them.
