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


def standardize(X_train, X_test):
    """Both sets rescaled with the training set's column means and standard
    deviations, as (X_train_scaled, X_test_scaled)."""
    mean, std = X_train.mean(axis=0), X_train.std(axis=0)
    return (X_train - mean) / std, (X_test - mean) / std


def train(X, y, lr=4.0, steps=1_000, l2=0.0):
    """Gradient descent from zero weights, as (w, b, losses), with the loss and its
    l2 term recorded after each step."""
    w, b = np.zeros(X.shape[1]), 0.0
    losses = []
    for _ in range(steps):
        dw, db = gradient(X, y, w, b, l2)
        w = w - lr * dw
        b = b - lr * db
        losses.append(log_loss(y, predict_proba(X, w, b)) + l2 / 2 * float(w @ w))
    return w, b, losses
