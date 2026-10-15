"""Ranking the bank's clients with a forest of decision trees."""

import numpy as np
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
    raise NotImplementedError


def grow_forest(X, said_yes, count, rng, min_leaf, max_features):
    """count trees, each grown on a bootstrap sample of the rows of X, and their samples."""
    raise NotImplementedError


def forest_score(trees, X):
    """Each row's share of yes, averaged over the trees."""
    raise NotImplementedError
