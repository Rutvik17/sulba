"""Logistic regression from scratch, in NumPy."""

import numpy as np


def sigmoid(z):
    """1 / (1 + e^-z), for a number or element by element for an array,
    without overflowing."""
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    positive = z >= 0
    out[positive] = 1.0 / (1.0 + np.exp(-z[positive]))
    ez = np.exp(z[~positive])
    out[~positive] = ez / (1.0 + ez)
    return out


def predict_proba(X, w, b):
    """The probability of class 1 for each row of X, with weights w and bias b."""
    return sigmoid(X @ w + b)


def log_loss(y, p):
    """The mean cross-entropy of labels y (0 or 1) and probabilities p,
    with p clipped to [1e-15, 1 - 1e-15]."""
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def gradient(X, y, w, b, l2=0.0):
    """The derivatives of log_loss(y, predict_proba(X, w, b)) + l2 / 2 * (w @ w)
    with respect to w and b, as (dw, db)."""
    error = predict_proba(X, w, b) - y
    return X.T @ error / len(y) + l2 * w, float(np.mean(error))
