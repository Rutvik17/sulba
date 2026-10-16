```python
def corrected_se(differences, n_fit, n_held):
    n = len(differences)
    return float(np.sqrt(np.var(differences, ddof=1) * (1 / n + n_held / n_fit)))


def interval(differences, n_fit, n_held, confidence):
    quantile = t.ppf((1 + confidence) / 2, len(differences) - 1)
    half = quantile * corrected_se(differences, n_fit, n_held)
    mean = float(np.mean(differences))
    return mean - half, mean + half
```

The folds fit on {% $fig.n_fit %} calls and hold out {% $fig.n_held %}, so over {% $fig.folds %} folds the corrected standard error is {% $fig.ratio %} times the usual one. With `$t$` = {% $fig.quantile %}, each model's {% $fig.confidence %} intervals for its difference from the baseline are:

| Model | Less the baseline | Usual interval | Corrected interval |
| --- | --- | --- | --- |
| Nearest neighbours | {% $fig.knn_diff %} | ± {% $fig.knn_usual %} | ± {% $fig.knn_corrected %} |
| Decision tree | {% $fig.tree_diff %} | ± {% $fig.tree_usual %} | ± {% $fig.tree_corrected %} |
| Random forest | {% $fig.forest_diff %} | ± {% $fig.forest_usual %} | ± {% $fig.forest_corrected %} |
| Gradient boosting | {% $fig.gb_diff %} | ± {% $fig.gb_usual %} | ± {% $fig.gb_corrected %} |

By the usual intervals, gradient boosting ranks the calls better than the baseline, and the tree worse. By the corrected ones, neither difference is clear: gradient boosting's interval runs from {% $fig.gb_low %} to {% $fig.gb_high %}, and the tree's from {% $fig.tree_low %} to {% $fig.tree_high %}.

More shuffles don't settle it. Here is gradient boosting against the baseline with more and more shuffles of the same calls:

| Shuffles | Folds | Less the baseline | Usual interval | Corrected interval |
| --- | --- | --- | --- | --- |
| {% $fig.r1 %} | {% $fig.r1_folds %} | {% $fig.r1_diff %} | ± {% $fig.r1_usual %} | ± {% $fig.r1_corrected %} |
| {% $fig.r2 %} | {% $fig.r2_folds %} | {% $fig.r2_diff %} | ± {% $fig.r2_usual %} | ± {% $fig.r2_corrected %} |
| {% $fig.r5 %} | {% $fig.r5_folds %} | {% $fig.r5_diff %} | ± {% $fig.r5_usual %} | ± {% $fig.r5_corrected %} |
| {% $fig.r10 %} | {% $fig.r10_folds %} | {% $fig.r10_diff %} | ± {% $fig.r10_usual %} | ± {% $fig.r10_corrected %} |

The usual interval narrows with every shuffle, and from {% $fig.r2 %} shuffles on it leaves 0 out. The corrected one levels off, since its second term doesn't shrink as folds are added: the corrected standard error never falls below {% $fig.floor %} of the differences' standard deviation. More folds of the same calls can't tell more than the calls hold.
