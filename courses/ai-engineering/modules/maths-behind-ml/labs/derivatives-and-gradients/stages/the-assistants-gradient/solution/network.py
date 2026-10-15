"""The clinic's network: its loss with weight decay, and the loss's gradient."""

import numpy as np


def loss(params, Z, y, l2=0.0):
    """The mean log loss of the network's probabilities, plus l2 / 2 times the sum of the
    squares of the weights in W1 and w2."""
    W1, b1, w2, b2 = params
    s = np.tanh(Z @ W1 + b1) @ w2 + b2
    data = np.mean(np.logaddexp(0, s) - y * s)
    return float(data + l2 / 2 * (np.sum(W1**2) + np.sum(w2**2)))


def gradient(params, Z, y, l2=0.0):
    """The derivatives of loss with respect to W1, b1, w2 and b2, in that order."""
    W1, b1, w2, b2 = params
    pre = Z @ W1 + b1
    hidden = np.tanh(pre)
    s = hidden @ w2 + b2
    ds = (1 / (1 + np.exp(-s)) - y) / len(y)
    dpre = np.outer(ds, w2) * (1 - hidden**2)
    dW1 = Z.T @ dpre + l2 * W1
    db1 = dpre.sum(axis=0)
    dw2 = hidden.T @ ds + l2 * w2
    db2 = float(ds.sum())
    return dW1, db1, dw2, db2
