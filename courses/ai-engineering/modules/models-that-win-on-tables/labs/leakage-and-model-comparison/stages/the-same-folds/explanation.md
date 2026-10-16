```python
def fold_scores(models, calls, said_yes, splits):
    table = {name: [] for name in models}
    for fit, held in splits:
        for name, model in models.items():
            fitted = clone(model).fit(calls.iloc[fit], said_yes[fit])
            chances = fitted.predict_proba(calls.iloc[held])[:, 1]
            table[name].append(roc_auc_score(said_yes[held], chances))
    return pd.DataFrame(table)


def differences(scores, baseline):
    return scores.drop(columns=baseline).sub(scores[baseline], axis=0)
```

Over {% $fig.folds %} folds, {% $fig.repeats %} shuffles of {% $fig.k %} folds of the {% $fig.calls %} calls, the five models rank the held-out calls like this:

| Model | Mean AUC | Lowest fold | Highest fold | Less the baseline | Folds above the baseline |
| --- | --- | --- | --- | --- | --- |
| Logistic regression | {% $fig.base_mean %} | {% $fig.base_low %} | {% $fig.base_high %} | | |
| Nearest neighbours | {% $fig.knn_mean %} | {% $fig.knn_low %} | {% $fig.knn_high %} | {% $fig.knn_diff %} | {% $fig.knn_wins %} |
| Decision tree | {% $fig.tree_mean %} | {% $fig.tree_low %} | {% $fig.tree_high %} | {% $fig.tree_diff %} | {% $fig.tree_wins %} |
| Random forest | {% $fig.forest_mean %} | {% $fig.forest_low %} | {% $fig.forest_high %} | {% $fig.forest_diff %} | {% $fig.forest_wins %} |
| Gradient boosting | {% $fig.gb_mean %} | {% $fig.gb_low %} | {% $fig.gb_high %} | {% $fig.gb_diff %} | {% $fig.gb_wins %} |

The folds differ more than the models do. The baseline's AUC runs from {% $fig.base_low %} on its hardest fold to {% $fig.base_high %} on its easiest, while gradient boosting's difference from it runs only from {% $fig.gb_diff_low %} to {% $fig.gb_diff_high %}. A fold that is hard for one model is hard for the other, and over the folds their AUCs have a correlation of {% $fig.gb_corr %}, so on the same folds each fold's difficulty cancels out of the difference. Scored on folds of its own, from another shuffle of the calls, gradient boosting's differences from the baseline would run from {% $fig.own_low %} to {% $fig.own_high %}, with a standard deviation of {% $fig.own_sd %} against {% $fig.same_sd %} on the same folds.
