This lab compares the module's models on the bank's calls, and a fair comparison starts with columns that don't hold the answer. The comparison cross-validates on the training and validation calls together, {% $fig.calls %} of them.

A client's job and education make {% $fig.pairs %} pairs among those calls, from {% $fig.top_pair %}, with {% $fig.top_calls %} calls, to {% $fig.rare %} pairs with fewer than {% $fig.rare_calls %}. Target encoding turns a category like this into one number: the share of its calls that said yes, pulled toward `$p$`, the share of all the calls, by a smoothing weight `$m$`. For a category of `$n$` calls, `$y$` of which said yes:

```math
S = \frac{y + m p}{n + m}
```

A category with few calls stays near `$p$`, one with many keeps close to its own share, and one the encoding never saw gets `$p$`.

A call's encoding can't be learnt from its own answer, or the column carries the answer a model is meant to predict. So the calls a model is scored on are encoded from the calls it is fitted on, and each of those fit calls is encoded from the calls outside its own fold: it is cross-fitted.

Start `encoding.py`. Write `encode` and `cross_fit`:

```
encode(fit_values, fit_yes, values, smooth) -> each value's encoding, learnt from the fit calls
cross_fit(values, said_yes, splits, smooth) -> each call's encoding, learnt outside its fold
```

`fit_values` and `values` are pandas Series of categories, and `fit_yes` and `said_yes` arrays of 1 for each call that said yes and 0 for each that said no. `splits` is a list of (fit, held) arrays of row numbers whose held rows take in every call once, and `cross_fit` encodes each split's held calls from its fit calls. Both return NumPy arrays. The tests compare yours with scikit-learn's `TargetEncoder`, whose `fit_transform` cross-fits.

The chart ranks the {% $fig.calls %} calls by their pair's encoding, learnt with each call's own answer and cross-fitted, for smoothing weights from 0 to {% $fig.most %}.
