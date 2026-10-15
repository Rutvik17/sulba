```python
def gradients(said_yes, share):
    """Each row's gradient and hessian of its log loss, at its share of yes."""
    return share - said_yes, share * (1 - share)


def leaf_weight(g, h, lam):
    """XGBoost's weight for a leaf of these rows."""
    return -g.sum() / (h.sum() + lam)


def split_gain(g, h, left, lam):
    """The gain XGBoost reports for splitting the rows into left and the rest."""

    def score(rows):
        return g[rows].sum() ** 2 / (h[rows].sum() + lam)

    return score(left) + score(~left) - score(np.ones(len(g), dtype=bool))


def best_split(X, g, h, lam, min_child_weight):
    """The column, threshold and gain of the best split of the rows into X[:, column] <
    threshold and the rest."""
    best = (None, None, -np.inf)
    for column in range(X.shape[1]):
        for threshold in np.unique(X[:, column])[1:]:
            left = X[:, column] < threshold
            if min(h[left].sum(), h[~left].sum()) < min_child_weight:
                continue
            gain = split_gain(g, h, left, lam)
            if gain > best[2]:
                best = (column, float(threshold), float(gain))
    return best
```

Your `boost` starts every call at the log-odds of the training calls' share of yes, {% $fig.share %}. XGBoost takes one Newton step from a share of a half instead, where every call's hessian is a quarter: a step of {% $fig.step %} in log-odds, which starts every call at a share of {% $fig.base %}. At that share, a call that said yes has a gradient of {% $fig.g_yes %}, one that said no {% $fig.g_no %}, and each a hessian of {% $fig.h %}.

XGBoost's first tree splits the calls on `pdays` below {% $fig.threshold %}. At its default `$\lambda$` of {% $fig.lam_0 %}, the calls on the left weigh {% $fig.cover_left %} in hessians and get a weight of {% $fig.left_0 %}, and those on the right weigh {% $fig.cover_right %} and get {% $fig.right_0 %}:

| `$\lambda$` | Gain | Left weight | Right weight |
| --- | --- | --- | --- |
| {% $fig.lam_0 %} | {% $fig.gain_0 %} | {% $fig.left_0 %} | {% $fig.right_0 %} |
| {% $fig.lam_1 %} | {% $fig.gain_1 %} | {% $fig.left_1 %} | {% $fig.right_1 %} |

`$\lambda$` is added to each leaf's sum of hessians, so it pulls a light leaf's weight towards 0 much more than a heavy one's: from {% $fig.lam_0 %} to {% $fig.lam_1 %}, the left weight shrinks by {% $fig.shrink_left %}, the right by {% $fig.shrink_right %}. Without `$\lambda$`, a weight is the Newton step your `boost` gives a leaf.

The hessians weigh the calls too: at {% $fig.h %} each, XGBoost's default `min_child_weight` of {% $fig.min_child_weight %} asks for at least {% $fig.min_calls %} calls in each part of a split, and more where the shares are near 0 or 1, whose hessians are small.

In the second-order view of the loss that XGBoost grows its trees by, a split lowers the loss by half the gain it reports, less `gamma`, a charge for each new leaf that is 0 unless it's set.
