Compare one split with five folds, then choose by cross-validation.

`holdout` makes one split by mix: the first of five folds, with `folds`. It returns a list of that one pair, so `fold_errors` scores it like any other list of splits. `choose` tries every degree and penalty it is given on the same splits, and returns the pair with the lowest mean RMSE over them, with that RMSE.

```
holdout(mixes, seed) -> [(fit, held)]
choose(X, y, splits, degrees, penalties) -> (degree, penalty, rmse)
```

Make each degree's features once, with `features`, and score every penalty on them with one call to `fold_errors`. The chart draws your estimates of one model's error with {% $fig.seeds %} different seeds, one split's and five folds', and the explanation compares the pairs each chooses.
