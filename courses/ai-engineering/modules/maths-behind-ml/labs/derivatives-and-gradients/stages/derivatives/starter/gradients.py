"""Derivatives and gradients, worked out numerically."""

import numpy as np


def forward_difference(f, x, h):
    """The slope of f from x to x + h: an estimate of f's derivative at x."""
    raise NotImplementedError


def central_difference(f, x, h):
    """The slope of f from x - h to x + h: an estimate of f's derivative at x."""
    raise NotImplementedError


def derivative(f, x):
    """f's derivative at x by a central difference, with a step of the cube root of
    float64's machine epsilon, times |x| when |x| is above 1."""
    raise NotImplementedError
