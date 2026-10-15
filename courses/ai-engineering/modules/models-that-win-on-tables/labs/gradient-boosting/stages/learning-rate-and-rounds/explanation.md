```python
def losses(model, X, said_yes):
    """The log loss on the rows after each round of a fitted GradientBoostingClassifier."""
    return np.array(
        [log_loss(said_yes, shares[:, 1]) for shares in model.staged_predict_proba(X)]
    )


def stop_early(history, patience):
    """The number of rounds to keep: up to the least loss before patience rounds in a row pass
    without a lower one."""
    best, since = 0, 0
    for round_ in range(1, len(history)):
        if history[round_] < history[best]:
            best, since = round_, 0
        else:
            since += 1
            if since == patience:
                break
    return best + 1
```

Trees of depth {% $fig.depth %}, {% $fig.rounds %} rounds of them, stopped early with a patience of {% $fig.patience %} on the {% $fig.validation %} validation calls:

| Learning rate | Rounds kept | Validation log loss there |
| --- | --- | --- |
| {% $fig.rate_0 %} | {% $fig.kept_0 %} | {% $fig.least_0 %} |
| {% $fig.rate_1 %} | {% $fig.kept_1 %} | {% $fig.least_1 %} |
| {% $fig.rate_2 %} | {% $fig.kept_2 %} | {% $fig.least_2 %} |
| {% $fig.rate_3 %} | {% $fig.kept_3 %} | {% $fig.least_3 %} |

Each tree's values are scaled by the rate, so a smaller rate moves the scores less in each round, and needs more rounds to reach its least loss. Small rates tend to reach a lower validation loss, and here the smallest rate's least loss is the lowest. Past its least, each rate's validation loss turns up again, as the chart shows.

At a rate of {% $fig.rate_0 %}, each tree adds its whole Newton steps, which overshoot: the training loss already rises in round {% $fig.first_rise %}, where at the smaller rates it falls in every one of the {% $fig.rounds %} rounds. And the least validation loss it reaches, {% $fig.least_0 %}, is no lower than the {% $fig.share_loss %} of giving every validation call the training calls' share of yes.

Early stopping makes the patience a rule: training stops once {% $fig.patience %} rounds in a row pass without a lower validation loss, and the model keeps the rounds up to the least. XGBoost's `early_stopping_rounds` stops this way when it has validation rows to watch, and its `predict` then uses only the rounds kept.
