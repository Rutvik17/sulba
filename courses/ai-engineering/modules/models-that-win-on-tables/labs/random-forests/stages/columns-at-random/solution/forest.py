"""Ranking the bank's clients with a forest of decision trees."""

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeClassifier

# The columns the trees read of each call: these numbers as they are, and these categories, a
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


def bootstrap(n, rng):
    """n row numbers drawn from 0 to n - 1, with replacement."""
    return rng.integers(0, n, size=n)


def grow_forest(X, said_yes, count, rng, min_leaf, max_features):
    """count trees, each grown on a bootstrap sample of the rows of X, and their samples."""
    trees, samples = [], []
    for _ in range(count):
        sample = bootstrap(len(X), rng)
        seed = int(rng.integers(2**31))
        tree = DecisionTreeClassifier(
            min_samples_leaf=min_leaf, max_features=max_features, random_state=seed
        )
        trees.append(tree.fit(X[sample], said_yes[sample]))
        samples.append(sample)
    return trees, samples


def forest_score(trees, X):
    """Each row's share of yes, averaged over the trees."""
    return np.mean([tree.predict_proba(X)[:, 1] for tree in trees], axis=0)


def auc_by_count(trees, X, said_yes):
    """The AUC of the forest of the first k trees, for each k from 1 to len(trees)."""
    shares = np.array([tree.predict_proba(X)[:, 1] for tree in trees])
    averages = np.cumsum(shares, axis=0) / np.arange(1, len(trees) + 1)[:, None]
    return np.array([roc_auc_score(said_yes, average) for average in averages])
