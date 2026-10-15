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
