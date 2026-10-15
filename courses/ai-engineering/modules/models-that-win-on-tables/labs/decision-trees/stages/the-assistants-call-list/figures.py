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
# The assistant's smallest leaf and depths.
MIN_LEAF = 25
DEPTHS = list(range(1, 13))


def encode(calls, categories, numbers):
    columns = [calls[name].to_numpy(dtype=float) for name in numbers]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


def best_split(column, said_yes, both_sides):
    order = np.argsort(column)
    values, labels = column[order], said_yes[order]
    calls = len(values)
    left = np.arange(1, calls)
    right = calls - left
    yes_left = np.cumsum(labels)[:-1]
    p, q = yes_left / left, (labels.sum() - yes_left) / right
    impurity = (left * 2 * p * (1 - p) + right * 2 * q * (1 - q)) / calls
    possible = (values[1:] > values[:-1]) & (left >= MIN_LEAF)
    if both_sides:
        possible &= right >= MIN_LEAF
    if not possible.any():
        return None
    i = np.flatnonzero(possible)[np.argmin(impurity[possible])]
    return (values[i] + values[i + 1]) / 2, impurity[i]


def grow(X, said_yes, depth, both_sides=True):
    node = {"calls": len(said_yes), "yes": int(said_yes.sum())}
    if depth == 0 or node["yes"] in (0, node["calls"]):
        return node
    splits = [best_split(X[:, j], said_yes, both_sides) for j in range(X.shape[1])]
    found = [(split[1], j, split[0]) for j, split in enumerate(splits) if split]
    if not found:
        return node
    _, column, threshold = min(found)
    left = X[:, column] <= threshold
    node.update(column=column, threshold=threshold)
    node["left"] = grow(X[left], said_yes[left], depth - 1, both_sides)
    node["right"] = grow(X[~left], said_yes[~left], depth - 1, both_sides)
    return node


def score(tree, X, depth):
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


def leaves(node, depth):
    if "column" not in node or depth == 0:
        return [node]
    return leaves(node["left"], depth - 1) + leaves(node["right"], depth - 1)


def figures():
    table = pd.read_csv("data/calls.csv")
    train, validation, test = (table[table["set"] == number] for number in (0, 1, 2))
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    said_yes = (train["subscribed"] == "yes").to_numpy()
    validation_yes = (validation["subscribed"] == "yes").to_numpy()

    def chosen(numbers, both_sides=True, on_validation=True):
        """The tree, its depth, and the validation AUC at each depth."""
        X = encode(train, categories, numbers)
        V = encode(validation, categories, numbers)
        tree = grow(X, said_yes, DEPTHS[-1], both_sides)
        validated = [roc_auc_score(validation_yes, score(tree, V, d)) for d in DEPTHS]
        trained = [roc_auc_score(said_yes, score(tree, X, d)) for d in DEPTHS]
        aucs = validated if on_validation else trained
        return tree, DEPTHS[int(np.argmax(aucs))], validated, trained

    found = {"min_leaf": str(MIN_LEAF)}
    # The call's length: the tree with it, and its ranking of calls whose length is unknown.
    with_length = ["age", "duration", "campaign", "pdays", "previous"]
    tree, depth, validated, _ = chosen(with_length)
    # Below the root's split on pdays, the clients the bank hadn't reached lately are split
    # by the call's length.
    root, node = tree, tree["right"]
    assert with_length[root["column"]] == "pdays"
    assert with_length[node["column"]] == "duration"
    rows = (train["pdays"] > root["threshold"]).to_numpy()
    longer = rows & (train["duration"] > node["threshold"]).to_numpy()
    shorter = rows & ~longer
    unknown = validation.assign(duration=0)
    blind = score(tree, encode(unknown, categories, with_length), depth)
    found |= {
        "pdays_t": f"{root['threshold']:g}",
        "length_t": f"{node['threshold']:g}",
        "longer": f"{longer.sum():,}",
        "longer_yes": f"{said_yes[longer].mean():.1%}",
        "shorter": f"{shorter.sum():,}",
        "shorter_yes": f"{said_yes[shorter].mean():.1%}",
        "length_auc": f"{validated[depth - 1]:.3f}",
        "blind_auc": f"{roc_auc_score(validation_yes, blind):.3f}",
    }
    # The depth chosen on the training calls, and on the validation calls.
    _, depth, validated, trained = chosen(NUMBERS, on_validation=False)
    _, best, _, _ = chosen(NUMBERS)
    found |= {
        "trained_depth": str(depth),
        "trained_train": f"{trained[depth - 1]:.3f}",
        "trained_validation": f"{validated[depth - 1]:.3f}",
        "best": str(best),
        "best_validation": f"{validated[best - 1]:.3f}",
    }
    # The smallest leaf kept on the left side only.
    tree, depth, _, _ = chosen(NUMBERS, both_sides=False)
    small = [leaf for leaf in leaves(tree, depth) if leaf["calls"] < MIN_LEAF]
    certain = [leaf for leaf in small if leaf["yes"] == leaf["calls"]]
    found |= {
        "left_depth": str(depth),
        "left_leaves": str(len(leaves(tree, depth))),
        "left_small": str(len(small)),
        "left_smallest": str(min(leaf["calls"] for leaf in small)),
        "left_certain": str(max(leaf["calls"] for leaf in certain)),
    }
    # A category the training calls never had.
    assert "yes" not in categories["default"]
    found |= {
        "test": f"{len(test):,}",
        "default_yes": str((test["default"] == "yes").sum()),
    }
    return found
