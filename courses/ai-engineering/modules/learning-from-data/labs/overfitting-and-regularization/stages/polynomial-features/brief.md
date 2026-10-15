Start `model.py`. A concrete plant wants to know a new mix's compressive strength, in megapascals (MPa), before it pours it. Each of its records is one test of a mix: how much of seven ingredients went into it, how old it was when it was tested, and the strength it reached.

A model with one weight per measurement adds the same strength for every day of age, at 3 days or at 300, and the same for every kilogram of water, however much cement the mix has. Polynomial features let it bend: products of the measurements, such as the age squared or the water times the cement, become features too, each with its own weight.

Write `features`, which returns every product of up to `degree` of the columns of `X`, and `rmse`, the root mean squared error of the predictions `y_hat` for the strengths `y`.

```
features(X, degree) -> one row per row of X, one column per product
rmse(y, y_hat) -> float
```

For two columns `$x_1$` and `$x_2$` and degree 2, the columns are `$x_1, x_2, x_1^2, x_1 x_2, x_2^2$`: the products of one column, then of two, each in the order `itertools.combinations_with_replacement` gives them. scikit-learn's `PolynomialFeatures(include_bias=False)` makes the same columns in the same order.

The tests use the lab's data: {% $fig.n_tests %} tests of {% $fig.n_mixes %} mixes. Each has eight measurements: the cement, blast furnace slag, fly ash, water, superplasticizer, coarse aggregate and fine aggregate, in kg per cubic metre of concrete, and the age at the test, in days.
