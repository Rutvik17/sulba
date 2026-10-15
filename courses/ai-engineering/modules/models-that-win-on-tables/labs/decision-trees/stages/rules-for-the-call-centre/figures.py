import numpy as np
import pandas as pd

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
# The tree the call centre reads: as deep, and with leaves as large, as the validation calls
# chose.
DEPTH, MIN_LEAF = 6, 25


def best_split(column, said_yes):
    order = np.argsort(column)
    values, labels = column[order], said_yes[order]
    calls = len(values)
    left = np.arange(1, calls)
    right = calls - left
    yes_left = np.cumsum(labels)[:-1]
    p, q = yes_left / left, (labels.sum() - yes_left) / right
    impurity = (left * 2 * p * (1 - p) + right * 2 * q * (1 - q)) / calls
    possible = (values[1:] > values[:-1]) & (left >= MIN_LEAF) & (right >= MIN_LEAF)
    if not possible.any():
        return None
    i = np.flatnonzero(possible)[np.argmin(impurity[possible])]
    return (values[i] + values[i + 1]) / 2, impurity[i]


def grow(X, said_yes, depth):
    node = {"calls": len(said_yes), "yes": int(said_yes.sum())}
    if depth == 0 or node["yes"] in (0, node["calls"]):
        return node
    splits = [best_split(X[:, j], said_yes) for j in range(X.shape[1])]
    found = [(split[1], j, split[0]) for j, split in enumerate(splits) if split]
    if not found:
        return node
    _, column, threshold = min(found)
    left = X[:, column] <= threshold
    node.update(column=column, threshold=threshold)
    node["left"] = grow(X[left], said_yes[left], depth - 1)
    node["right"] = grow(X[~left], said_yes[~left], depth - 1)
    return node


def paths(node, columns, conditions):
    """Each leaf with the conditions on its path, in the tree's order."""
    if "column" not in node:
        return [(conditions, node)]
    column, threshold = columns[node["column"]], node["threshold"]
    left, right = dict(conditions), dict(conditions)
    if isinstance(column, tuple):
        name, category = column
        _, ruled_out = conditions.get(name, ("is not", []))
        left[name] = ("is not", sorted([*ruled_out, category]))
        right[name] = ("is", category)
    else:
        low, high = conditions.get(column, (-np.inf, np.inf))
        left[column] = (low, min(high, threshold))
        right[column] = (max(low, threshold), high)
    return paths(node["left"], columns, left) + paths(node["right"], columns, right)


def meets(calls, conditions):
    met = np.ones(len(calls), dtype=bool)
    for name, (first, second) in conditions.items():
        if first == "is":
            met &= (calls[name] == second).to_numpy()
        elif first == "is not":
            met &= ~calls[name].isin(second).to_numpy()
        else:
            met &= ((calls[name] > first) & (calls[name] <= second)).to_numpy()
    return met


def figures():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    columns = NUMBERS + [(name, c) for name in CATEGORIES for c in categories[name]]
    X = [train[name].to_numpy(dtype=float) for name in NUMBERS]
    X += [
        (train[name] == c).to_numpy(dtype=float) for name, c in columns[len(NUMBERS) :]
    ]
    said_yes = (train["subscribed"] == "yes").to_numpy()
    tree = grow(np.column_stack(X), said_yes, DEPTH)
    found = sorted(
        paths(tree, columns, {}), key=lambda rule: -rule[1]["yes"] / rule[1]["calls"]
    )
    top, leaf = found[0]
    assert list(top) == ["pdays", "education"]
    assert top["education"] == ("is", "university.degree")
    biggest, big = max(found, key=lambda rule: rule[1]["calls"])
    zero = [conditions for conditions, leaf in found if leaf["yes"] == 0]
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    zero_met = np.any([meets(validation, conditions) for conditions in zero], axis=0)
    return {
        "validation": f"{len(validation):,}",
        "depth": str(DEPTH),
        "min_leaf": str(MIN_LEAF),
        "rules": str(len(found)),
        "top_low": f"{top['pdays'][0]:g}",
        "top_high": f"{top['pdays'][1]:g}",
        "top_yes": str(leaf["yes"]),
        "top_calls": str(leaf["calls"]),
        "big_calls": f"{big['calls']:,}",
        "big_share": f"{big['yes'] / big['calls']:.1%}",
        "big_columns": str(len(biggest)),
        "zero_rules": str(len(zero)),
        "zero_calls": str(sum(leaf["calls"] for _, leaf in found if leaf["yes"] == 0)),
        "zero_validation": str(zero_met.sum()),
        "zero_validation_yes": str((zero_met & validation_yes).sum()),
    }
