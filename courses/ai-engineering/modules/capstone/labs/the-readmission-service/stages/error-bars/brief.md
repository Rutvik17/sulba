Stage 2's AUC came from one split of the stays: one draw of {% $fig.test %} held out. A different draw would give a different number, and a choice made on one draw can be made on luck. Measure the model the way every later choice will be measured: by cross-validation, with an error bar.

Add to `model.py`:

```
cross_validated(table, make=make_model, folds=5) -> each fold's AUC: a new model from make()
    fitted to the other folds' stays and scored on the fold's
summary(aucs) -> (mean, standard error) of the AUCs
```

The folds come from `StratifiedKFold(folds, shuffle=True, random_state=SEED)`, so each keeps the share readmitted. Fit each fold's model with `scores`, on a new model from `make()`, and score it with `auc`. `make` lets the same folds test any model: stage 5 compares two.

The standard error of the mean is the AUCs' standard deviation, with `ddof=1`, over the square root of how many there are:

```math
\text{SE} = \frac{s}{\sqrt{k}}
```

| Symbol | Meaning |
| --- | --- |
| `$s$` | The standard deviation of the fold AUCs, dividing by `$k - 1$` |
| `$k$` | The number of folds |

The tests compare your fold AUCs with scikit-learn's `cross_val_score` on the same folds.
