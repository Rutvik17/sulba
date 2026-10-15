import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeRegressor

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
# The model the explanation grows: its rounds, rate and depth.
ROUNDS, RATE, DEPTH = 50, 0.1, 3


def encode(calls, categories):
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


def figures():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    names = NUMBERS + [f"{name} {c}" for name in CATEGORIES for c in categories[name]]
    X, V = encode(train, categories), encode(validation, categories)
    said_yes = (train["subscribed"] == "yes").to_numpy()
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    share = said_yes.mean()
    log_odds = np.full(len(X), np.log(share / (1 - share)))
    scores = np.full(len(V), log_odds[0])
    for round_ in range(ROUNDS):
        p = expit(log_odds)
        residual = said_yes - p
        tree = DecisionTreeRegressor(
            criterion="friedman_mse", max_depth=DEPTH, random_state=0
        )
        tree.fit(X, residual)
        leaves = tree.apply(X)
        values = np.zeros(tree.tree_.node_count)
        for leaf in np.unique(leaves):
            here = leaves == leaf
            values[leaf] = residual[here].sum() / (p[here] * (1 - p[here])).sum()
        if round_ == 0:
            first, first_values, first_leaves = tree, values, leaves
        log_odds = log_odds + RATE * values[leaves]
        scores = scores + RATE * values[tree.apply(V)]
        if round_ == 0:
            first_auc = roc_auc_score(validation_yes, scores)
    # The explanation names the first tree's first split, and the leaf of 50 calls or more
    # whose calls most often said yes.
    assert names[first.tree_.feature[0]] == "pdays"
    large = [
        leaf for leaf in np.unique(first_leaves) if (first_leaves == leaf).sum() >= 50
    ]
    most = max(large, key=lambda leaf: said_yes[first_leaves == leaf].mean())
    here = first_leaves == most
    return {
        "train": f"{len(X):,}",
        "share": f"{share:.1%}",
        "start": f"{np.log(share / (1 - share)):.3f}".replace("-", "−"),
        "residual_yes": f"{1 - share:.3f}",
        "residual_no": f"{-share:.3f}".replace("-", "−"),
        "spread": f"{share * (1 - share):.4f}",
        "root": f"{first.tree_.threshold[0]:g}",
        "leaf_calls": str(int(here.sum())),
        "leaf_yes": str(int(said_yes[here].sum())),
        "leaf_residual": f"{(said_yes[here] - share).mean():.3f}",
        "leaf_value": f"{first_values[most]:.3f}",
        "rate": f"{RATE:g}",
        "leaf_step": f"{RATE * first_values[most]:.3f}",
        "rounds": str(ROUNDS),
        "depth": str(DEPTH),
        "first_auc": f"{first_auc:.3f}",
        "train_auc": f"{roc_auc_score(said_yes, log_odds):.3f}",
        "validation_auc": f"{roc_auc_score(validation_yes, scores):.3f}",
    }
