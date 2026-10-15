"""Cross-validation of the plant's strength models, over whole mixes."""

from itertools import combinations_with_replacement

import numpy as np


def features(X, degree):
    """Every product of up to `degree` of the columns of X, as in the last lab."""
    return np.column_stack(
        [
            np.prod(X[:, list(columns)], axis=1)
            for size in range(1, degree + 1)
            for columns in combinations_with_replacement(range(X.shape[1]), size)
        ]
    )


def ridge(Z, y, penalties):
    """Ridge regression on standardized features Z, as in the last lab: one (w, b) for each
    penalty, with the bias left out of the penalty."""
    mean = Z.mean(axis=0)
    centered = Z - mean
    gram = centered.T @ centered
    right = centered.T @ (y - y.mean())
    n, d = Z.shape
    fits = []
    for penalty in penalties:
        w = np.linalg.solve(gram + n * penalty * np.eye(d), right)
        fits.append((w, float(y.mean() - mean @ w)))
    return fits


def folds(mixes, k, seed):
    """The tests to fit on and to hold out in each of k folds, with every test of a mix in
    its mix's fold."""
    raise NotImplementedError


def fold_errors(P, y, splits, penalties):
    """Each fold's RMSE on its held-out tests at each penalty: one row per fold, one column
    per penalty."""
    raise NotImplementedError
