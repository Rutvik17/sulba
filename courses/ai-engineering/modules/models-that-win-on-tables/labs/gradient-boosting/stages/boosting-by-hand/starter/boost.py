"""Ranking the bank's clients with boosted trees."""

import numpy as np
from scipy.special import expit
from sklearn.tree import DecisionTreeRegressor

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


def start(said_yes):
    """The log-odds of the share of yes among the calls."""
    raise NotImplementedError


def boost(X, said_yes, rounds, rate, depth):
    """A model of rounds trees, each fitted to the residuals of the trees before it."""
    raise NotImplementedError


def boost_score(model, X):
    """Each row's log-odds of yes: the start, plus rate times each tree's value for it."""
    raise NotImplementedError
