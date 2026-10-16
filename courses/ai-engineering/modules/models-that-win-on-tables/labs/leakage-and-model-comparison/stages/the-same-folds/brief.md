The bank wants the model that ranks its call list best, and has five to choose from: the module's four, and a logistic regression as the baseline, the simple model each of them has to beat. `models` in the starter builds them, each a pipeline from the calls' columns to a chance of yes:

| Model | Settings |
| --- | --- |
| Logistic regression | The baseline, on standardized numbers |
| Nearest neighbours | {% $fig.neighbours %} neighbours by Manhattan distance, the sum of the columns' absolute differences, on standardized numbers |
| Decision tree | At least {% $fig.tree_leaf %} calls a leaf |
| Random forest | {% $fig.trees %} trees, at least {% $fig.forest_leaf %} calls a leaf |
| Gradient boosting | LightGBM, {% $fig.rounds %} rounds at a learning rate of {% $fig.rate %}, {% $fig.leaves %} leaves a tree |

One split can't tell them apart: which calls happen to be held out moves every model's AUC more than the models differ. The comparison repeats k-fold cross-validation with new shuffles of the calls, and scores every model on the same folds: on each fold, every model is fitted on the same calls and ranks the same held-out calls. The difference between two models' AUCs on a fold then measures the models rather than the fold.

Start `compare.py`. Write `fold_scores` and `differences`:

```
fold_scores(models, calls, said_yes, splits) -> a DataFrame: a row per split, a column per model
differences(scores, baseline) -> each other model's AUC less the baseline's, split by split
```

`models` maps each model's name to its pipeline, and `splits` is a list of (fit, held) arrays of row numbers. For each split, `fold_scores` fits a fresh copy of each model, from `sklearn.base.clone`, on the fit calls, and puts its AUC on the held calls in the model's column, the columns in the order of `models`. `differences` gives a DataFrame with a column for each model but the baseline. The explanation scores the five models on {% $fig.repeats %} shuffles of {% $fig.k %} folds of the {% $fig.calls %} calls, from scikit-learn's `RepeatedStratifiedKFold`.
