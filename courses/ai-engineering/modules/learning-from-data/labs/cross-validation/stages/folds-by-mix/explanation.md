k-fold cross-validation predicts every test once, with a model fit on the other folds, and its estimate is the mean of the folds' errors:

```math
\text{CV}_k = \frac{1}{k} \sum_{i=1}^{k} \text{RMSE}_i
```

| Symbol | Meaning |
| --- | --- |
| `$k$` | The number of folds |
| `$\text{RMSE}_i$` | The error on fold `$i$`'s held-out tests, of the model fit on the other folds |

Worked example, 5 folds with seed 0, at degree 3 with `$\lambda = \fig{penalty}$`:

| Fold | Mixes | Tests | RMSE |
| --- | --- | --- | --- |
| 1 | {% $fig.mixes_1 %} | {% $fig.tests_1 %} | {% $fig.rmse_1 %} MPa |
| 2 | {% $fig.mixes_2 %} | {% $fig.tests_2 %} | {% $fig.rmse_2 %} MPa |
| 3 | {% $fig.mixes_3 %} | {% $fig.tests_3 %} | {% $fig.rmse_3 %} MPa |
| 4 | {% $fig.mixes_4 %} | {% $fig.tests_4 %} | {% $fig.rmse_4 %} MPa |
| 5 | {% $fig.mixes_5 %} | {% $fig.tests_5 %} | {% $fig.rmse_5 %} MPa |
| Mean | | | {% $fig.mean %} MPa |

The folds hold nearly the same number of mixes, but not of tests, since some mixes were tested at more ages than others.

A product of measurements has nothing to learn from the data, so the features are made once for every test. The standardization learns a mean and a spread, so each fold takes them from its fit tests alone. Taken from every test, they would carry the held-out tests into the model that predicts them.

More folds fit each model on more of the records, nine tenths of them at `$k = 10$`, so its error is closer to that of a model fit on all of them. But the folds' models then share more of their fit tests, so their errors move together, and an average of errors that move together varies more from one shuffle to another. Five and ten folds are the usual choices between the two.
