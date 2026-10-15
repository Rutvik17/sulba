```python
def start(said_yes):
    """The log-odds of the share of yes among the calls."""
    share = np.mean(said_yes)
    return float(np.log(share / (1 - share)))


def boost(X, said_yes, rounds, rate, depth):
    """A model of rounds trees, each fitted to the residuals of the trees before it."""
    model = {"start": start(said_yes), "rate": rate, "trees": [], "values": []}
    log_odds = np.full(len(X), model["start"])
    for _ in range(rounds):
        share = expit(log_odds)
        residual = said_yes - share
        tree = DecisionTreeRegressor(
            criterion="friedman_mse", max_depth=depth, random_state=0
        )
        tree.fit(X, residual)
        leaves = tree.apply(X)
        values = np.zeros(tree.tree_.node_count)
        for leaf in np.unique(leaves):
            here = leaves == leaf
            spread = share[here] * (1 - share[here])
            values[leaf] = residual[here].sum() / spread.sum()
        log_odds = log_odds + rate * values[leaves]
        model["trees"].append(tree)
        model["values"].append(values)
    return model


def boost_score(model, X):
    """Each row's log-odds of yes: the start, plus rate times each tree's value for it."""
    log_odds = np.full(len(X), model["start"])
    for tree, values in zip(model["trees"], model["values"], strict=True):
        log_odds = log_odds + model["rate"] * values[tree.apply(X)]
    return log_odds
```

Every call starts at the log-odds of the share of yes among the {% $fig.train %} training calls, {% $fig.share %}: {% $fig.start %}. In the first round every share is the same, so a call that said yes has a residual of {% $fig.residual_yes %} and one that said no {% $fig.residual_no %}. The first tree, fitted to those residuals, splits the calls first on `pdays`, at {% $fig.root %} days.

A leaf's value is a step in the log-odds, not a share. As a step `$v$` is added to the log-odds of a leaf's calls, their log loss has a slope of `$\sum (p - y)$` and a curvature of `$\sum p(1 - p)$` at `$v = 0$`. The leaf's value is the step Newton's method takes towards the least loss, the slope's negative over the curvature: `$\sum (y - p) / \sum p(1 - p)$`.

In the first round, every call's `$p(1 - p)$` is {% $fig.spread %}, so a leaf's value is its mean residual over {% $fig.spread %}. The leaf of {% $fig.leaf_calls %} calls, {% $fig.leaf_yes %} of which said yes, has a mean residual of {% $fig.leaf_residual %} and a value of {% $fig.leaf_value %}, so a rate of {% $fig.rate %} raises its calls' log-odds by {% $fig.leaf_step %}.

Each round's tree fits the residuals the trees before it left, so the model keeps working on the calls it still scores worst. After {% $fig.rounds %} rounds of depth {% $fig.depth %}, it ranks the validation calls at an AUC of {% $fig.validation_auc %}, from {% $fig.first_auc %} after its first tree, and its own training calls at {% $fig.train_auc %}.
