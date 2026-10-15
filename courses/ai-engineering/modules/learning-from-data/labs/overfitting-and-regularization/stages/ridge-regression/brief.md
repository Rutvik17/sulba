Add ridge regression to `model.py`: least squares with a cost for large weights, so a flexible model can't use them to fit noise.

`ridge` returns the weights and the bias that minimize the mean squared error plus `penalty * (w @ w)`. The bias isn't penalized. `choose` tries every degree and penalty it is given, fits ridge regression on the training mixes' standardized features, and returns the pair with the lowest validation RMSE, with that RMSE.

```
ridge(P, y, penalty) -> (w, b)
choose(X_train, y_train, X_val, y_val, degrees, penalties) -> (degree, penalty, val_rmse)
```

Your weights must match scikit-learn's `Ridge(alpha=len(y) * penalty)` within 0.00000001, and `choose` must find the same pair as scikit-learn among degrees 1 to 3 and penalties from 0.00001 to 1.
