Start `cv.py`. In the last lab one validation split chose the model, and the plant's records are few: {% $fig.tests %} tests of {% $fig.mixes %} mixes, the last lab's training and validation sets together. Which mixes a single split holds out changes the error it measures. k-fold cross-validation holds out every mix once: it deals the mixes into k folds, and for each fold it fits a model on the other folds and measures the error on the fold's own tests.

Write `folds`, which shuffles the mix numbers with `np.random.default_rng(seed).permutation(np.unique(mixes))` and deals them to the folds in turn: the first to fold 0, the next to fold 1, and back to fold 0 after fold `k - 1`. Every test of a mix goes in its mix's fold. It returns a pair for each fold, in order: the row numbers to fit on and the row numbers held out, each from lowest to highest.

Then write `fold_errors`, which scores ridge regression on the features `P` in each fold. It standardizes with the column means and standard deviations of the fold's fit tests, fits with `ridge` at every penalty, and returns the RMSE on the held-out tests.

```
folds(mixes, k, seed) -> [(fit, held), ...], one pair per fold
fold_errors(P, y, splits, penalties) -> one row per fold, one column per penalty
```

`features` and `ridge` are written for you, as in the last lab. The test set, {% $fig.test_tests %} tests of {% $fig.test_mixes %} mixes, stays out of the records.
