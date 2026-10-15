"""Linear regression from scratch, in NumPy."""

import numpy as np


def predict(X, w, b):
    """The forecast for each row of X: the weighted sum of its features, plus b."""
    raise NotImplementedError


def mse(y, y_hat):
    """The mean squared error of the forecasts y_hat for the outputs y."""
    raise NotImplementedError
