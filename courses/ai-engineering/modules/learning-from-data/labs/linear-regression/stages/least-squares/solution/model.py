"""Linear regression from scratch, in NumPy."""

import numpy as np


def predict(X, w, b):
    """The forecast for each row of X: the weighted sum of its features, plus b."""
    return X @ w + b


def mse(y, y_hat):
    """The mean squared error of the forecasts y_hat for the outputs y."""
    return float(np.mean((np.asarray(y, dtype=float) - y_hat) ** 2))


def fit(X, y):
    """The weights and bias with the least mean squared error on X and y, as (w, b)."""
    A = np.column_stack([X, np.ones(len(X))])
    theta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return theta[:-1], float(theta[-1])
