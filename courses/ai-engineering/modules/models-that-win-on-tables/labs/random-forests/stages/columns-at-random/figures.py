import collections

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
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
# The forests the explanation grows: their trees, their smallest leaf and their seed, and the
# trees the chart grows.
TREES, MIN_LEAF, SEED, CHART_TREES = 50, 10, 0, 40


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
    found = {
        "trees": str(TREES),
        "min_leaf": str(MIN_LEAF),
        "columns": str(X.shape[1]),
        "sqrt": str(int(np.sqrt(X.shape[1]))),
        "chart_trees": str(CHART_TREES),
    }
    means, forests = {}, {}
    for key, max_features in [("every", None), ("random", "sqrt")]:
        rng = np.random.default_rng(SEED)
        roots, shares, each = collections.Counter(), [], []
        for _ in range(TREES):
            sample = rng.integers(0, len(X), size=len(X))
            tree = DecisionTreeClassifier(
                min_samples_leaf=MIN_LEAF,
                max_features=max_features,
                random_state=int(rng.integers(2**31)),
            )
            tree.fit(X[sample], said_yes[sample])
            roots[names[tree.tree_.feature[0]]] += 1
            shares.append(tree.predict_proba(V)[:, 1])
            each.append(roc_auc_score(validation_yes, shares[-1]))
        top, count = roots.most_common(1)[0]
        # The explanation names the column most trees split first.
        assert top == {"every": "pdays", "random": "previous"}[key]
        found[f"{key}_top_count"] = str(count)
        found[f"{key}_roots"] = str(len(roots))
        means[key] = np.mean(each)
        forests[key] = roc_auc_score(validation_yes, np.mean(shares, axis=0))
        found[f"{key}_tree"] = f"{means[key]:.3f}"
        found[f"{key}_forest"] = f"{forests[key]:.3f}"
    # The explanation says the trees with columns drawn at random do no worse alone, on
    # average, and better averaged.
    assert means["random"] >= means["every"]
    assert forests["random"] > forests["every"]
    return found
