"""Ranking a bank's clients by their chance of saying yes, with a decision tree."""

import numpy as np


def gini(yes, calls):
    """The Gini impurity of calls calls of which yes said yes."""
    share = yes / calls
    return 2 * share * (1 - share)


def best_split(column, said_yes, min_leaf):
    """The threshold on column that leaves the least impurity, and that impurity. Calls at or
    below the threshold go left, and each side keeps at least min_leaf calls. None when no
    threshold does."""
    order = np.argsort(column)
    values, labels = column[order], said_yes[order]
    calls = len(values)
    # The calls on each side of a threshold after each position, and the yes among them.
    left = np.arange(1, calls)
    right = calls - left
    yes_left = np.cumsum(labels)[:-1]
    yes_right = labels.sum() - yes_left
    impurity = (left * gini(yes_left, left) + right * gini(yes_right, right)) / calls
    # A threshold lies between two different values and leaves min_leaf calls on each side.
    possible = (values[1:] > values[:-1]) & (left >= min_leaf) & (right >= min_leaf)
    if not possible.any():
        return None
    i = np.flatnonzero(possible)[np.argmin(impurity[possible])]
    return (values[i] + values[i + 1]) / 2, impurity[i]
