Fit the model. `fit` returns the weights and the bias with the least mean squared error on the hours it is given, found exactly, in one step.

```
fit(X, y) -> (w, b)
```

On the training hours, your weights must match scikit-learn's `LinearRegression` within 0.00000001, and your forecasts must match its forecasts within 0.000001 MW on every test hour. `fit` must also work when one column repeats another.
