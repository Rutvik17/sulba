import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

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
DEPTHS = list(range(1, 13))
# The smallest leaf the explanation chooses the depth for, and the other two it compares.
MIN_LEAF, ONE, BIG = 25, 1, 100


def encode(calls, categories):
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


def best_split(column, said_yes, min_leaf):
    order = np.argsort(column)
    values, labels = column[order], said_yes[order]
    calls = len(values)
    left = np.arange(1, calls)
    right = calls - left
    yes_left = np.cumsum(labels)[:-1]
    yes_right = labels.sum() - yes_left
    share_left, share_right = yes_left / left, yes_right / right
    impurity = (
        left * 2 * share_left * (1 - share_left)
        + right * 2 * share_right * (1 - share_right)
    ) / calls
    possible = (values[1:] > values[:-1]) & (left >= min_leaf) & (right >= min_leaf)
    if not possible.any():
        return None
    i = np.flatnonzero(possible)[np.argmin(impurity[possible])]
    return (values[i] + values[i + 1]) / 2, impurity[i]


def grow(X, said_yes, depth, min_leaf):
    node = {"calls": len(said_yes), "yes": int(said_yes.sum())}
    if depth == 0 or node["yes"] in (0, node["calls"]):
        return node
    best = None
    for column in range(X.shape[1]):
        found = best_split(X[:, column], said_yes, min_leaf)
        if found is not None and (best is None or found[1] < best[2]):
            best = (column, *found)
    if best is None:
        return node
    column, threshold, _ = best
    left = X[:, column] <= threshold
    node["column"], node["threshold"] = column, threshold
    node["left"] = grow(X[left], said_yes[left], depth - 1, min_leaf)
    node["right"] = grow(X[~left], said_yes[~left], depth - 1, min_leaf)
    return node


def score(tree, X, depth):
    """Each row's share of yes in the leaf it reaches in tree cut at depth."""
    shares = np.empty(len(X))

    def visit(node, rows, level):
        if "column" not in node or level == depth:
            shares[rows] = node["yes"] / node["calls"]
            return
        below = X[rows, node["column"]] <= node["threshold"]
        visit(node["left"], rows[below], level + 1)
        visit(node["right"], rows[~below], level + 1)

    visit(tree, np.arange(len(X)), 0)
    return shares


def figures():
    table = pd.read_csv("data/calls.csv")
    parts = [table[table["set"] == number] for number in (0, 1, 2)]
    categories = {name: sorted(parts[0][name].unique()) for name in CATEGORIES}
    X, V, T = (encode(part, categories) for part in parts)
    said_yes, validation_yes, test_yes = (
        (part["subscribed"] == "yes").to_numpy() for part in parts
    )

    def aucs(min_leaf):
        tree = grow(X, said_yes, DEPTHS[-1], min_leaf)
        trained = [roc_auc_score(said_yes, score(tree, X, d)) for d in DEPTHS]
        validated = [roc_auc_score(validation_yes, score(tree, V, d)) for d in DEPTHS]
        best = DEPTHS[int(np.argmax(validated))]
        test = roc_auc_score(test_yes, score(tree, T, best))
        return trained, validated, best, test

    trained, validated, best, test = aucs(MIN_LEAF)
    one_trained, one_validated, _, _ = aucs(ONE)
    _, big_validated, big_best, big_test = aucs(BIG)
    at = DEPTHS.index(best)
    return {
        "min_leaf": str(MIN_LEAF),
        "best": str(best),
        "best_validation": f"{validated[at]:.3f}",
        "best_training": f"{trained[at]:.3f}",
        "deepest": str(DEPTHS[-1]),
        "deep_training": f"{trained[-1]:.3f}",
        "deep_validation": f"{validated[-1]:.3f}",
        "one": str(ONE),
        "one_training": f"{one_trained[-1]:.3f}",
        "one_validation": f"{one_validated[-1]:.3f}",
        "big_leaf": str(BIG),
        "big_best": str(big_best),
        "big_validation": f"{big_validated[DEPTHS.index(big_best)]:.3f}",
        "test": f"{test:.3f}",
        "big_test": f"{big_test:.3f}",
    }
