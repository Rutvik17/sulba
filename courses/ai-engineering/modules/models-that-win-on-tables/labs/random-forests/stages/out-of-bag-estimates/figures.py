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
# The forest the explanation grows, and the counts of trees it follows the left-out calls
# by, the fifth of them the few trees it estimates a forest of.
TREES, MIN_LEAF, SEED = 100, 10, 0
FEW = [1, 2, 5, 10]
SMALL = 5


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
    X, V = encode(train, categories), encode(validation, categories)
    said_yes = (train["subscribed"] == "yes").to_numpy()
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    rng = np.random.default_rng(SEED)
    total, count = np.zeros(len(X)), np.zeros(len(X))
    scores, seen, never = [], [], {}
    for k in range(1, TREES + 1):
        sample = rng.integers(0, len(X), size=len(X))
        tree = DecisionTreeClassifier(
            min_samples_leaf=MIN_LEAF,
            max_features="sqrt",
            random_state=int(rng.integers(2**31)),
        )
        tree.fit(X[sample], said_yes[sample])
        left_out = np.ones(len(X), dtype=bool)
        left_out[sample] = False
        total[left_out] += tree.predict_proba(X[left_out])[:, 1]
        count[left_out] += 1
        scores.append(tree.predict_proba(V)[:, 1])
        seen.append(tree.predict_proba(X)[:, 1])
        if k in FEW:
            never[k] = (count == 0).mean()
        if k == SMALL:
            scored = count > 0
            small_oob = roc_auc_score(said_yes[scored], total[scored] / count[scored])
            small_validation = roc_auc_score(validation_yes, np.mean(scores, axis=0))
    oob = total / count
    # The explanation says the five trees' estimate runs below their forest.
    assert small_oob < small_validation
    found = {
        "trees": str(TREES),
        "min_leaf": str(MIN_LEAF),
        "oob": f"{roc_auc_score(said_yes, oob):.3f}",
        "validation": f"{roc_auc_score(validation_yes, np.mean(scores, axis=0)):.3f}",
        "in_sample": f"{roc_auc_score(said_yes, np.mean(seen, axis=0)):.3f}",
    }
    for i, k in enumerate(FEW):
        found[f"few_{i}"] = str(k)
        found[f"never_{i}"] = f"{never[k]:.1%}"
    found["small"] = str(SMALL)
    found["small_oob"] = f"{small_oob:.3f}"
    found["small_validation"] = f"{small_validation:.3f}"
    return found
