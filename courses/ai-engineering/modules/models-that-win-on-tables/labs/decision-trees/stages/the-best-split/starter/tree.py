"""Ranking a bank's clients by their chance of saying yes, with a decision tree."""

import numpy as np


def gini(yes, calls):
    """The Gini impurity of calls calls of which yes said yes."""
    raise NotImplementedError


def best_split(column, said_yes, min_leaf):
    """The threshold on column that leaves the least impurity, and that impurity. Calls at or
    below the threshold go left, and each side keeps at least min_leaf calls. None when no
    threshold does."""
    raise NotImplementedError
