"""Tomorrow's call list: the bank's clients in the order to call them, the likeliest first."""

import numpy as np
from sklearn.metrics import roc_auc_score

# What the tree reads of each call: these numbers, and a column for each category of these.
NUMBERS = ["age", "duration", "campaign", "pdays", "previous"]
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
# The fewest training calls in a leaf, and the depths to choose among.
MIN_LEAF = 25
DEPTHS = list(range(1, 13))


def encode(calls, categories):
    """The calls as an array: the numbers, then a column of 0 and 1 for each category."""
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        codes = np.array([categories[name].index(value) for value in calls[name]])
        for code in range(len(categories[name])):
            columns.append((codes == code).astype(float))
    return np.column_stack(columns)


def labelled(calls, categories):
    """The calls encoded, and whether each said yes."""
    return encode(calls, categories), (calls["subscribed"] == "yes").to_numpy()


def best_split(column, said_yes, min_leaf):
    """The best threshold on column and the impurity it leaves, or None."""
    order = np.argsort(column)
    values, labels = column[order], said_yes[order]
    calls = len(values)
    left = np.arange(1, calls)
    right = calls - left
    yes_left = np.cumsum(labels)[:-1]
    p, q = yes_left / left, (labels.sum() - yes_left) / right
    impurity = (left * 2 * p * (1 - p) + right * 2 * q * (1 - q)) / calls
    possible = (values[1:] > values[:-1]) & (left >= min_leaf)
    if not possible.any():
        return None
    i = np.flatnonzero(possible)[np.argmin(impurity[possible])]
    return (values[i] + values[i + 1]) / 2, impurity[i]


def grow(X, said_yes, depth, min_leaf=MIN_LEAF):
    """A tree grown on the rows of X, at most depth splits deep."""
    node = {"calls": len(said_yes), "yes": int(said_yes.sum())}
    if depth == 0 or node["yes"] in (0, node["calls"]):
        return node
    splits = [best_split(X[:, j], said_yes, min_leaf) for j in range(X.shape[1])]
    found = [(split[1], j, split[0]) for j, split in enumerate(splits) if split]
    if not found:
        return node
    _, column, threshold = min(found)
    left = X[:, column] <= threshold
    node.update(column=column, threshold=threshold)
    node["left"] = grow(X[left], said_yes[left], depth - 1, min_leaf)
    node["right"] = grow(X[~left], said_yes[~left], depth - 1, min_leaf)
    return node


def prune(tree, depth):
    """tree cut at depth."""
    if depth == 0 or "column" not in tree:
        return {"calls": tree["calls"], "yes": tree["yes"]}
    left, right = prune(tree["left"], depth - 1), prune(tree["right"], depth - 1)
    return {**tree, "left": left, "right": right}


def score(tree, X):
    """Each row's share of yes in the leaf it reaches."""
    shares = np.empty(len(X))
    for i, row in enumerate(X):
        node = tree
        while "column" in node:
            below = row[node["column"]] <= node["threshold"]
            node = node["left"] if below else node["right"]
        shares[i] = node["yes"] / node["calls"]
    return shares


def choose_depth(tree, X, said_yes):
    """The smallest of DEPTHS at which tree, cut there, ranks the calls of X best."""
    aucs = [roc_auc_score(said_yes, score(prune(tree, depth), X)) for depth in DEPTHS]
    return DEPTHS[int(np.argmax(aucs))]


def fit(train, validation):
    """The call list's tree, grown on the training calls and cut at the depth that ranks the
    validation calls best, and the categories it reads."""
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    tree = grow(*labelled(train, categories), max(DEPTHS))
    depth = choose_depth(tree, *labelled(train, categories))
    return prune(tree, depth), categories


def call_list(fitted, clients):
    """The clients' row labels in the order to call them, and their shares of yes."""
    tree, categories = fitted
    shares = score(tree, encode(clients, categories))
    order = np.argsort(-shares, kind="stable")
    return clients.index[order], shares[order]
