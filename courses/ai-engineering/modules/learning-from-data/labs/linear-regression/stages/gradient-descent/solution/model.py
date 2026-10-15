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


def standardize(X_train, X_test):
    """Both sets rescaled with the training set's column means and standard
    deviations, as (X_train_scaled, X_test_scaled)."""
    mean, std = X_train.mean(axis=0), X_train.std(axis=0)
    return (X_train - mean) / std, (X_test - mean) / std


def gradient(X, y, w, b):
    """The derivatives of mse(y, predict(X, w, b)) with respect to w and b, as
    (dw, db)."""
    error = predict(X, w, b) - y
    return 2 * X.T @ error / len(y), 2 * float(np.mean(error))


def train(X, y, lr=0.3, steps=500):
    """Gradient descent from zero weights and the mean output as the bias, as
    (w, b, losses), with the loss recorded after each step."""
    w, b = np.zeros(X.shape[1]), float(np.mean(y))
    losses = []
    for _ in range(steps):
        dw, db = gradient(X, y, w, b)
        w = w - lr * dw
        b = b - lr * db
        losses.append(mse(y, predict(X, w, b)))
    return w, b, losses
