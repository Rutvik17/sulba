```python
def encode(fit_values, fit_yes, values, smooth):
    prior = np.mean(fit_yes)
    groups = pd.Series(fit_yes).groupby(fit_values.to_numpy())
    shares = (groups.sum() + smooth * prior) / (groups.count() + smooth)
    return values.map(shares).fillna(prior).to_numpy(dtype=float)


def cross_fit(values, said_yes, splits, smooth):
    encoded = np.empty(len(values))
    for fit, held in splits:
        encoded[held] = encode(
            values.iloc[fit], said_yes[fit], values.iloc[held], smooth
        )
    return encoded
```

Ranked by their pair's encoding learnt with each call's own answer, the {% $fig.calls %} calls have an AUC of {% $fig.own_auc %}. Cross-fitted, they have {% $fig.crossed_auc %}, and the difference is the leak. A call's own answer moves its pair's encoding by `$1 / (n + m)$`, up for a yes and down for a no, and most in the smallest pairs. The pair {% $fig.example %} holds a single call, which said yes: learnt from it with `$m$` = {% $fig.smooth %}, the pair's encoding is {% $fig.example_yes %}, and had the call said no it would be {% $fig.example_no %}. The {% $fig.example_move %} between them is the answer itself. Smoothing doesn't remove the leak, as the chart shows: at `$m$` = {% $fig.most %}, {% $fig.own_most %} against {% $fig.crossed_most %}. Leaving each call's answer out does.

Over {% $fig.folds %} folds, a logistic regression on the columns the earlier labs read ranks the held-out calls at a mean AUC of {% $fig.baseline %}. With the pair's encoding added, learnt in each fold from its fit calls, it ranks them at {% $fig.inside %}: the pair adds nothing the job and education columns don't. Learnt from all {% $fig.calls %} calls before the folds, the encoding takes in each held-out call's own answer, and the same model ranks them at {% $fig.leaked %}, a gain that comes from the leak alone.
