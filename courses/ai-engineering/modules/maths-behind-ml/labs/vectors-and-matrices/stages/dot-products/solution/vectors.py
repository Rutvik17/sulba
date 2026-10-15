"""Vectors and matrices for the clinic's records."""

import numpy as np


def dot(a, b):
    """The dot product of two vectors: the sum of their elementwise products."""
    return float(np.sum(a * b))


def norm(a):
    """A vector's length: the square root of its dot product with itself."""
    return float(np.sqrt(dot(a, a)))


def cosine(a, b):
    """The cosine of the angle between two vectors."""
    return dot(a, b) / (norm(a) * norm(b))


def centroids(Z, y):
    """The mean of the rows of Z where y is 0, then the mean of the rows where y is 1."""
    return np.mean(Z[y == 0], axis=0), np.mean(Z[y == 1], axis=0)
