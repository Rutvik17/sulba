Fit a model at each degree on the training mixes, and score it on the validation mixes.

`standardize` rescales both sets with the training set's column means and standard deviations. `fit` returns the weights and the bias with the least mean squared error, found exactly with `np.linalg.lstsq`. `errors` makes the features of `degree` for both sets, standardizes them, fits on the training set, and returns the RMSE on each set.

```
standardize(P_train, P_other) -> (P_train_scaled, P_other_scaled)
fit(P, y) -> (w, b)
errors(X_train, y_train, X_val, y_val, degree) -> (train_rmse, val_rmse)
```

The lab's mixes are split three ways, every test of a mix in the same set: {% $fig.train_tests %} tests of {% $fig.train_mixes %} mixes for training, {% $fig.val_tests %} tests of {% $fig.val_mixes %} mixes for validation, and {% $fig.test_tests %} tests of {% $fig.test_mixes %} mixes for the final test. At every degree up to 3, your errors must match scikit-learn's within 0.000001 MPa.
