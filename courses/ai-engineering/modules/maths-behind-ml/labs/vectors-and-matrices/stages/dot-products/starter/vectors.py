"""Vectors and matrices for the clinic's records."""

import numpy as np


def dot(a, b):
    """The dot product of two vectors: the sum of their elementwise products."""
    raise NotImplementedError


def norm(a):
    """A vector's length: the square root of its dot product with itself."""
    raise NotImplementedError


def cosine(a, b):
    """The cosine of the angle between two vectors."""
    raise NotImplementedError


def centroids(Z, y):
    """The mean of the rows of Z where y is 0, then the mean of the rows where y is 1."""
    raise NotImplementedError
