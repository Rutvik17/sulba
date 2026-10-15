Start `model.py`. A linear regression model forecasts a number as a weighted sum of the features, plus a bias. Here it forecasts the net electrical output of a gas and steam power plant, in megawatts (MW), for each hour from that hour's weather.

Write `predict`, which returns one forecast per row of `X`, and `mse`, the mean squared error of the forecasts `y_hat` for the actual outputs `y`.

```
predict(X, w, b) -> one forecast per row of X
mse(y, y_hat) -> float
```

The tests use the lab's data: {% $fig.n_train %} training hours and {% $fig.n_test %} test hours, each with {% $fig.n_features %} measurements: the temperature, the exhaust vacuum, the air pressure and the relative humidity.
