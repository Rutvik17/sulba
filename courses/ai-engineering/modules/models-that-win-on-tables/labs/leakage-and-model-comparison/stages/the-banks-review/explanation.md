```python
def review(scores, baseline, n_fit, n_held, confidence):
    others = differences(scores, baseline)
    each = 1 - (1 - confidence) / len(others.columns)
    rows = {}
    for name in others.columns:
        low, high = interval(others[name], n_fit, n_held, each)
        rows[name] = {
            "difference": float(others[name].mean()),
            "low": low,
            "high": high,
            "beats": bool(low > 0),
        }
    return pd.DataFrame.from_dict(rows, orient="index")


def choose(scores, baseline, n_fit, n_held, confidence):
    table = review(scores, baseline, n_fit, n_held, confidence)
    winners = table[table["beats"]]
    if winners.empty:
        return baseline
    return winners["difference"].idxmax()


def latest(model, calls, said_yes, share):
    start = len(calls) - round(len(calls) * share)
    fitted = clone(model).fit(calls.iloc[:start], said_yes[:start])
    chances = fitted.predict_proba(calls.iloc[start:])[:, 1]
    return float(roc_auc_score(said_yes[start:], chances))
```

The bank's review of the module's four models, with the {% $fig.confidence %} shared among them, each interval at {% $fig.each %}:

| Model | Less the baseline | Interval | Beats the baseline |
| --- | --- | --- | --- |
| Nearest neighbours | {% $fig.knn_diff %} | {% $fig.knn_low %} to {% $fig.knn_high %} | {% $fig.knn_beats %} |
| Decision tree | {% $fig.tree_diff %} | {% $fig.tree_low %} to {% $fig.tree_high %} | {% $fig.tree_beats %} |
| Random forest | {% $fig.forest_diff %} | {% $fig.forest_low %} to {% $fig.forest_high %} | {% $fig.forest_beats %} |
| Gradient boosting | {% $fig.gb_diff %} | {% $fig.gb_low %} to {% $fig.gb_high %} | {% $fig.gb_beats %} |

No candidate beats the baseline, so the bank keeps the logistic regression.

The latest calls bear the choice out. Fitted on the first {% $fig.fit_calls %} of the bank's {% $fig.all_calls %} calls and scored on the last {% $fig.last_calls %}:

| Model | Mean AUC on the folds | AUC on the latest calls |
| --- | --- | --- |
| Logistic regression | {% $fig.base_folds %} | {% $fig.base_latest %} |
| Nearest neighbours | {% $fig.knn_folds %} | {% $fig.knn_latest %} |
| Decision tree | {% $fig.tree_folds %} | {% $fig.tree_latest %} |
| Random forest | {% $fig.forest_folds %} | {% $fig.forest_latest %} |
| Gradient boosting | {% $fig.gb_folds %} | {% $fig.gb_latest %} |

Every model ranks the latest calls less well than its mean on the folds, and the baseline ranks them best. The calls changed over time: {% $fig.first_yes %} of the first {% $fig.last_calls %} said yes, and {% $fig.last_yes %} of the last {% $fig.last_calls %}. Shuffled folds mix calls from every month, so they measure how well a model ranks calls like the ones it learnt from. The latest calls measure how well it ranks the calls that come after, which is how the bank will use it.
