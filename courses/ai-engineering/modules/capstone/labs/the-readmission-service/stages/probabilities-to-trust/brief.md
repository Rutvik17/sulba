The planners will read the service's answer as a chance: of the stays it gives 20%, about one in five should come back. An AUC says nothing about that, only about the order. Check the probabilities themselves, on stays the model never learned from.

Add to `model.py`:

```
out_of_fold(table, make=make_model, folds=5) -> each stay's probability from the fold model,
    made by make(), that didn't learn from it, in the order of table's rows
calibration(y, probabilities, bins=10) -> (predicted, observed): for groups of stays ranked by
    probability, each group's mean probability and the share of it readmitted
brier(y, probabilities) -> the mean of (probability - y) squared, with y 1 or 0
```

`out_of_fold` uses the folds `cross_validated` uses, and fits each fold's model with `scores`. Every stay is held out once, so each gets one probability, from a model that never saw it.

`calibration` makes its groups as scikit-learn's `calibration_curve` does with `strategy="quantile"`. The edges are the probabilities' quantiles, `np.quantile(probabilities, np.linspace(0, 1, bins + 1))`. Each stay goes in group `np.searchsorted(edges[1:-1], probability)`, and a group no stay falls in is left out.

The tests compare your functions with `cross_val_predict`, `calibration_curve` and `brier_score_loss`.
