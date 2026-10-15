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
