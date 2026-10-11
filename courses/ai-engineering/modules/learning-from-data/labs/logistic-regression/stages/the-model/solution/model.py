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
