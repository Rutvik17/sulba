import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

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
# The smallest leaf, the depth of the tree the explanation lists, and the depth of the larger
# tree it counts the leaves of.
MIN_LEAF, SMALL_DEPTH, DEPTH = 25, 2, 6


def figures():
    table = pd.read_csv("data/calls.csv")
    train, test = table[table["set"] == 0], table[table["set"] == 2]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    names = NUMBERS + [f"{name}={c}" for name in CATEGORIES for c in categories[name]]
    columns = [train[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        columns += [(train[name] == c).to_numpy(dtype=float) for c in categories[name]]
    X, said_yes = np.column_stack(columns), (train["subscribed"] == "yes").to_numpy()

    small = DecisionTreeClassifier(max_depth=SMALL_DEPTH, min_samples_leaf=MIN_LEAF)
    nodes = small.fit(X, said_yes).tree_

    def describe(rows):
        return f"{rows.sum():,} calls, {said_yes[rows].mean():.1%} yes"

    # The root's split, and each side's, on the columns the explanation names.
    assert names[nodes.feature[0]] == "pdays"
    left = X[:, nodes.feature[0]] <= nodes.threshold[0]
    found = {
        "min_leaf": str(MIN_LEAF),
        "small_depth": str(SMALL_DEPTH),
        "small_leaves": str(nodes.n_leaves),
        "root_t": f"{nodes.threshold[0]:g}",
        "left": describe(left),
        "right": describe(~left),
    }
    for key, i, rows, column in [
        ("left", nodes.children_left[0], left, "pdays"),
        ("right", nodes.children_right[0], ~left, "age"),
    ]:
        assert names[nodes.feature[i]] == column
        below = X[:, nodes.feature[i]] <= nodes.threshold[i]
        found[f"{key}_t"] = f"{nodes.threshold[i]:g}"
        found[f"{key}_left"] = describe(rows & below)
        found[f"{key}_right"] = describe(rows & ~below)
    deeper = DecisionTreeClassifier(max_depth=DEPTH, min_samples_leaf=MIN_LEAF).fit(
        X, said_yes
    )
    found["depth"] = str(DEPTH)
    found["leaves"] = str(deeper.get_n_leaves())
    found["numbers"] = str(len(NUMBERS))
    found["category_columns"] = str(len(CATEGORIES))
    found["categories"] = str(sum(len(c) for c in categories.values()))
    found["columns"] = str(X.shape[1])
    found["default_test"] = str((test["default"] == "yes").sum())
    assert categories["default"] == ["no", "unknown"]
    return found
