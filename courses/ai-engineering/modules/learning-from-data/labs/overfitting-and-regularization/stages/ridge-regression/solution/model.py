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


def standardize(P_train, P_other):
    """Both sets rescaled with the training set's column means and standard deviations,
    as (P_train_scaled, P_other_scaled)."""
    mean, std = P_train.mean(axis=0), P_train.std(axis=0)
    return (P_train - mean) / std, (P_other - mean) / std


def fit(P, y):
    """The weights and bias with the least mean squared error on P and y, as (w, b)."""
    A = np.column_stack([P, np.ones(len(P))])
    theta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return theta[:-1], float(theta[-1])


def errors(X_train, y_train, X_val, y_val, degree):
    """The training and validation RMSE of least squares on features of `degree`, as
    (train_rmse, val_rmse)."""
    P_train, P_val = standardize(features(X_train, degree), features(X_val, degree))
    w, b = fit(P_train, y_train)
    return rmse(y_train, P_train @ w + b), rmse(y_val, P_val @ w + b)


def ridge(P, y, penalty):
    """The weights and bias with the least mean squared error plus penalty * (w @ w),
    the bias not penalized, as (w, b)."""
    mean = P.mean(axis=0)
    centered = P - mean
    n, d = P.shape
    w = np.linalg.solve(
        centered.T @ centered + n * penalty * np.eye(d), centered.T @ (y - y.mean())
    )
    return w, float(y.mean() - mean @ w)


def choose(X_train, y_train, X_val, y_val, degrees, penalties):
    """The degree and penalty whose ridge regression has the lowest validation RMSE,
    with that RMSE, as (degree, penalty, val_rmse)."""
    best = None
    for degree in degrees:
        P_train, P_val = standardize(features(X_train, degree), features(X_val, degree))
        for penalty in penalties:
            w, b = ridge(P_train, y_train, penalty)
            score = rmse(y_val, P_val @ w + b)
            if best is None or score < best[2]:
                best = (degree, penalty, score)
    return best
