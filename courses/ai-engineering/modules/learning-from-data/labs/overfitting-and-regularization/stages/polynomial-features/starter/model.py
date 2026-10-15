"""Polynomial regression with a penalty, from scratch, in NumPy."""

from itertools import combinations_with_replacement

import numpy as np


def features(X, degree):
    """Every product of up to `degree` of X's columns: the columns, then each product of
    two, and so on, one column each."""
    raise NotImplementedError


def rmse(y, y_hat):
    """The root mean squared error of the predictions y_hat for the strengths y."""
    raise NotImplementedError
