"""Ranking a bank's clients by their chance of saying yes, with a decision tree."""

import numpy as np


def gini(yes, calls):
    """The Gini impurity of calls calls of which yes said yes."""
    share = yes / calls
    return 2 * share * (1 - share)


def best_split(column, said_yes, min_leaf):
    """The threshold on column that leaves the least impurity, and that impurity. Calls at or
    below the threshold go left, and each side keeps at least min_leaf calls. None when no
    threshold does."""
    order = np.argsort(column)
    values, labels = column[order], said_yes[order]
    calls = len(values)
    # The calls on each side of a threshold after each position, and the yes among them.
    left = np.arange(1, calls)
    right = calls - left
    yes_left = np.cumsum(labels)[:-1]
    yes_right = labels.sum() - yes_left
    impurity = (left * gini(yes_left, left) + right * gini(yes_right, right)) / calls
    # A threshold lies between two different values and leaves min_leaf calls on each side.
    possible = (values[1:] > values[:-1]) & (left >= min_leaf) & (right >= min_leaf)
    if not possible.any():
        return None
    i = np.flatnonzero(possible)[np.argmin(impurity[possible])]
    return (values[i] + values[i + 1]) / 2, impurity[i]


# The columns the tree reads of each call: these numbers as they are, and these categories, a
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


def grow(X, said_yes, depth, min_leaf):
    """A tree grown on the rows of X, with at most depth splits from its root to a leaf."""
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
    node["column"], node["threshold"] = column, float(threshold)
    node["left"] = grow(X[left], said_yes[left], depth - 1, min_leaf)
    node["right"] = grow(X[~left], said_yes[~left], depth - 1, min_leaf)
    return node


def score(tree, X):
    """For each row of X, the share of yes in the leaf it reaches."""
    shares = []
    for row in X:
        node = tree
        while "column" in node:
            below = row[node["column"]] <= node["threshold"]
            node = node["left"] if below else node["right"]
        shares.append(node["yes"] / node["calls"])
    return np.array(shares)
