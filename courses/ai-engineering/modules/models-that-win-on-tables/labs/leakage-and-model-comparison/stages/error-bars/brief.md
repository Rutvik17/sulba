Gradient boosting's AUC is {% $fig.gb_lead %} above the baseline's on average over the {% $fig.folds %} folds. An interval around that mean says how far it could be from the difference on other calls. The usual standard error of a mean, `$s / \sqrt{n}$` for `$n$` values with a standard deviation of `$s$`, assumes the values are independent, and the folds' differences aren't: any two folds fit their models on calls that are {% $fig.shared %} the same, on average, so the models are much alike and their differences move together.

Nadeau and Bengio's correction allows for that. It takes the correlation between two folds' differences to be the share of the calls a fold holds out, which gives, for folds of `$n_\text{fit}$` calls fitted on and `$n_\text{held}$` held out:

```math
\text{SE} = s \sqrt{\frac{1}{n} + \frac{n_\text{held}}{n_\text{fit}}}
```

The interval at a confidence `$c$` is the mean difference plus and minus `$t \cdot \text{SE}$`, where `$t$` is the quantile of the t distribution with `$n - 1$` degrees of freedom at `$(1 + c) / 2$`, which leaves `$(1 - c) / 2$` of the distribution beyond each end.

Write `corrected_se` and `interval`, and import `numpy as np`, and `t` from `scipy.stats`, at the top of `compare.py`:

```
corrected_se(differences, n_fit, n_held) -> the corrected standard error of the mean difference
interval(differences, n_fit, n_held, confidence) -> (low, high)
```

`differences` holds one model's differences from the baseline, one for each fold, and `t.ppf(q, df)` gives the t distribution's quantile at `q`.
