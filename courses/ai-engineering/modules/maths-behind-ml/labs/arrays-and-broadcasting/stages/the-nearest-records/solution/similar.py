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


def standardize(X, mean, std):
    """X with each column less its mean and divided by its standard deviation, as
    StandardScaler's transform gives it: a column whose standard deviation is 0 is
    divided by 1."""
    return (X - mean) / np.where(std == 0, 1, std)


def distances(A, B):
    """The Euclidean distance from each row of A to each row of B, as an array of shape
    (len(A), len(B))."""
    return np.sqrt(np.sum((A[:, None, :] - B[None, :, :]) ** 2, axis=-1))


def nearest(D, k):
    """The column numbers of the k smallest distances in each row of D, smallest first,
    with equal distances in column order: an array of shape (len(D), k)."""
    return np.argsort(D, axis=1, kind="stable")[:, :k]


def malignant_share(near, diagnoses):
    """For each row of near, the share of the records it names that are malignant."""
    return np.mean(diagnoses[near], axis=1)
