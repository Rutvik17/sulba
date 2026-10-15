"""Measures of the survey's pulsar classifier."""

import numpy as np


def roc_curve(y, scores):
    """The false and true positive rates at each threshold, from np.inf down through
    each distinct score, as scikit-learn's roc_curve gives them with
    drop_intermediate=False."""
    raise NotImplementedError


def roc_auc(y, scores):
    """The area under the ROC curve, by the trapezoid rule."""
    raise NotImplementedError
