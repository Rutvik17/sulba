Train the model by gradient descent, the way models too large to solve in one step are trained.

`standardize` rescales both sets with the training set's column means and standard deviations, so every column of the training set has mean 0 and standard deviation 1. The test set uses the training set's numbers, not its own.

`gradient` returns the derivatives of the mean squared error with respect to the weights and the bias, as `(dw, db)`.

`train` starts with zero weights and the bias at the mean output, then takes `steps` steps of gradient descent, `w = w - lr * dw` and `b = b - lr * db`. After each step it records the mean squared error, and it returns `(w, b, losses)`.

```
standardize(X_train, X_test) -> (X_train_scaled, X_test_scaled)
gradient(X, y, w, b) -> (dw, db)
train(X, y, lr=0.3, steps=500) -> (w, b, losses)
```

With the defaults, on the standardized hours, your forecasts must match least squares within 0.01 MW on every test hour.
