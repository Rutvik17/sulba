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


def direction(mu0, mu1):
    """The vector of length 1 that points from mu0 to mu1."""
    w = mu1 - mu0
    return w / norm(w)


def scores(Z, mu0, mu1):
    """Each row of Z's signed distance from the midpoint of mu0 and mu1, along the
    direction from mu0 to mu1: positive on mu1's side of the midpoint."""
    return (Z - (mu0 + mu1) / 2) @ direction(mu0, mu1)


def pairwise_dots(A, B):
    """The dot product of each row of A with each row of B, as an array of shape
    (len(A), len(B))."""
    return A @ B.T


def fast_distances(A, B):
    """The Euclidean distance from each row of A to each row of B, worked out from the
    dot products: each squared distance is a row's squared length, plus the other row's,
    less twice their dot product, and one below 0 counts as 0."""
    squared = (
        np.sum(A**2, axis=1)[:, None]
        + np.sum(B**2, axis=1)[None, :]
        - 2 * pairwise_dots(A, B)
    )
    return np.sqrt(np.maximum(squared, 0))
