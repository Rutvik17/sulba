"""Logistic regression from scratch, in NumPy."""

import numpy as np


def sigmoid(z):
    """1 / (1 + e^-z), for a number or element by element for an array,
    without overflowing."""
    raise NotImplementedError


def predict_proba(X, w, b):
    """The probability of class 1 for each row of X, with weights w and bias b."""
    raise NotImplementedError
