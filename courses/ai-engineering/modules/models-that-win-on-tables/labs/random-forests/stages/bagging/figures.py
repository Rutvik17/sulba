import math

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
# The forest the explanation grows: its trees, and the seed of its generator.
TREES, SEED = 50, 0


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
    scores, distinct = [], []
    for _ in range(TREES):
        sample = rng.integers(0, len(X), size=len(X))
        tree = DecisionTreeClassifier(random_state=int(rng.integers(2**31)))
        tree.fit(X[sample], said_yes[sample])
        scores.append(tree.predict_proba(V)[:, 1])
        distinct.append(len(np.unique(sample)) / len(X))
    each = [roc_auc_score(validation_yes, score) for score in scores]
    forest = roc_auc_score(validation_yes, np.mean(scores, axis=0))
    # The explanation shows the average ranking the calls better than any of its trees.
    assert forest > max(each)
    return {
        "train": f"{len(X):,}",
        "distinct": f"{np.mean(distinct):.1%}",
        "limit": f"{1 - 1 / math.e:.1%}",
        "trees": str(TREES),
        "tree_low": f"{min(each):.3f}",
        "tree_high": f"{max(each):.3f}",
        "tree_mean": f"{np.mean(each):.3f}",
        "forest": f"{forest:.3f}",
    }
