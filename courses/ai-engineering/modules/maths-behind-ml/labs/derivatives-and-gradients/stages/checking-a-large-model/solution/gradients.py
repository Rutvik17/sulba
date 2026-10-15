"""Derivatives and gradients, worked out numerically."""

import numpy as np


def forward_difference(f, x, h):
    """The slope of f from x to x + h: an estimate of f's derivative at x."""
    return (f(x + h) - f(x)) / h


def central_difference(f, x, h):
    """The slope of f from x - h to x + h: an estimate of f's derivative at x."""
    return (f(x + h) - f(x - h)) / (2 * h)


def derivative(f, x):
    """f's derivative at x by a central difference, with a step of the cube root of
    float64's machine epsilon, times |x| when |x| is above 1."""
    h = np.cbrt(np.finfo(np.float64).eps) * max(1.0, abs(x))
    return central_difference(f, x, h)


def numerical_gradient(f, x, h=1e-6):
    """The gradient of f at the vector x: a central difference for each element in turn,
    leaving x as it was."""
    gradient = np.zeros(len(x))
    for i in range(len(x)):
        axis = np.zeros(len(x))
        axis[i] = 1.0
        gradient[i] = central_difference(lambda t: f(x + t * axis), 0.0, h)
    return gradient


def relative_error(a, b):
    """The length of a - b as a share of the longer of a and b, or 0 when both are 0."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    longer = max(np.sqrt(np.sum(a**2)), np.sqrt(np.sum(b**2)))
    return 0.0 if longer == 0 else float(np.sqrt(np.sum((a - b) ** 2)) / longer)


def network_loss(params, Z, y):
    """The mean log loss of a network with one hidden layer of tanh units. params is
    (W1, b1, w2, b2), each row of Z is a sample, and y holds the diagnoses, 0 or 1."""
    W1, b1, w2, b2 = params
    s = np.tanh(Z @ W1 + b1) @ w2 + b2
    return float(np.mean(np.logaddexp(0, s) - y * s))


def network_gradient(params, Z, y):
    """The derivatives of network_loss with respect to W1, b1, w2 and b2, by the chain
    rule: a tuple in that order, each of its parameter's shape."""
    W1, b1, w2, b2 = params
    hidden = np.tanh(Z @ W1 + b1)
    s = hidden @ w2 + b2
    # The loss's slope along each sample's score: its probability less its diagnosis.
    ds = (np.exp(-np.logaddexp(0, -s)) - y) / len(y)
    # Back through w2 to the hidden layer, then through tanh, whose slope is 1 - tanh².
    dpre = np.outer(ds, w2) * (1 - hidden**2)
    return Z.T @ dpre, dpre.sum(axis=0), hidden.T @ ds, float(ds.sum())


def directional_slope(f, x, v, h=1e-6):
    """f's slope at x along the vector v, by a central difference."""
    return central_difference(lambda t: f(x + t * v), 0.0, h)


def gradient_agrees(f, gradient, x, rng, directions=8, tolerance=1e-6):
    """Whether gradient(x) gives f's slope at x along random directions drawn from rng."""
    g = np.asarray(gradient(x), dtype=float)
    length = np.sqrt(np.sum(g**2))
    for _ in range(directions):
        v = rng.normal(size=len(x))
        v /= np.sqrt(np.sum(v**2))
        measured = directional_slope(f, x, v)
        # Against the gradient's length, since along a random direction g @ v can be near 0.
        if abs(g @ v - measured) > tolerance * max(length, abs(measured)):
            return False
    return True
