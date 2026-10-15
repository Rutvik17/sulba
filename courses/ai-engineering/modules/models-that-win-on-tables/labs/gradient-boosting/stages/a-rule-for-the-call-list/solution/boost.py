"""Ranking the bank's clients with boosted trees."""

import numpy as np
from lightgbm import LGBMClassifier, early_stopping
from scipy.special import expit
from sklearn.metrics import log_loss
from sklearn.tree import DecisionTreeRegressor

# The columns the trees read of each call: these numbers as they are, and these categories, a
# column for each of their categories.
NUMBERS = ["age", "campaign", "pdays", "previous"]
CATEGORIES = [
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "poutcome",
]


def encode(calls, categories):
    """The calls as an array: the number columns as they are, then a column for each category
    in categories, 1 for the calls in it and 0 for the rest."""
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


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


# LightGBM's rounds at most, its learning rate and leaves a tree, and the rounds in a row
# without a lower validation log loss after which it stops.
ROUNDS, RATE, LEAVES, PATIENCE = 500, 0.05, 8, 20


def frame(calls):
    """The columns the model reads: the numbers as they are, then each category column as a
    pandas category."""
    columns = calls[NUMBERS + CATEGORIES].copy()
    for name in CATEGORIES:
        columns[name] = columns[name].astype("category")
    return columns


def call_model(train, validation, rule):
    """LightGBM on the training calls, stopped early on the validation calls, and with rule, a
    chance that never rises with campaign."""
    rules = {}
    if rule:
        rules["monotone_constraints"] = [
            -1 if name == "campaign" else 0 for name in NUMBERS + CATEGORIES
        ]
    model = LGBMClassifier(
        n_estimators=ROUNDS, learning_rate=RATE, num_leaves=LEAVES, verbose=-1, **rules
    )
    model.fit(
        frame(train),
        (train["subscribed"] == "yes").to_numpy(),
        eval_set=[(frame(validation), (validation["subscribed"] == "yes").to_numpy())],
        callbacks=[early_stopping(PATIENCE, verbose=False)],
    )
    return model


def raised(model, clients, more):
    """How many clients the model would give a higher chance after up to more calls more."""
    now = model.predict_proba(frame(clients))[:, 1]
    higher = np.zeros(len(clients), dtype=bool)
    for extra in range(1, more + 1):
        later = clients.copy()
        later["campaign"] = later["campaign"] + extra
        higher |= model.predict_proba(frame(later))[:, 1] > now
    return int(higher.sum())
