"""Polynomial regression with a penalty, from scratch, in NumPy."""

from itertools import combinations_with_replacement

import numpy as np


def features(X, degree):
    """Every product of up to `degree` of X's columns: the columns, then each product of
    two, and so on, one column each."""
    X = np.asarray(X, dtype=float)
    products = [
        np.prod(X[:, list(columns)], axis=1)
        for size in range(1, degree + 1)
        for columns in combinations_with_replacement(range(X.shape[1]), size)
    ]
    return np.column_stack(products)


def rmse(y, y_hat):
    """The root mean squared error of the predictions y_hat for the strengths y."""
    return float(np.sqrt(np.mean((np.asarray(y, dtype=float) - y_hat) ** 2)))
