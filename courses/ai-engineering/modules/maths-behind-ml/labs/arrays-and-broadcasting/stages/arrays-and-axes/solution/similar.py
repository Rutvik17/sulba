"""Finds the records most like each new sample."""

import numpy as np


def split(table):
    """The records' measurements and diagnoses, then the new samples' measurements and
    diagnoses. A row with 0 in column 0 is a record, and a row with 1 a new sample."""
    new = table[:, 0] == 1
    return table[~new, 2:], table[~new, 1], table[new, 2:], table[new, 1]


def column_stats(X):
    """Each column's mean and standard deviation over the rows of X, as scikit-learn's
    StandardScaler computes them."""
    return np.mean(X, axis=0), np.std(X, axis=0)
