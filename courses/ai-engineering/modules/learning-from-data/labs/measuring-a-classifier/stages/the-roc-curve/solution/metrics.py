"""Measures of the survey's pulsar classifier."""

import numpy as np


def roc_curve(y, scores):
    """The false and true positive rates at each threshold, from np.inf down through
    each distinct score, as scikit-learn's roc_curve gives them with
    drop_intermediate=False."""
    y = np.asarray(y)
    scores = np.asarray(scores, dtype=float)
    order = np.argsort(-scores, kind="stable")
    ranked = scores[order]
    pulsars = np.cumsum(y[order] == 1)
    others = np.cumsum(y[order] != 1)
    # The last candidate with each score: candidates with the same score cross together.
    last = np.flatnonzero(np.append(ranked[1:] != ranked[:-1], True))
    fpr = np.concatenate([[0.0], others[last] / others[-1]])
    tpr = np.concatenate([[0.0], pulsars[last] / pulsars[-1]])
    thresholds = np.concatenate([[np.inf], ranked[last]])
    return fpr, tpr, thresholds


def roc_auc(y, scores):
    """The area under the ROC curve, by the trapezoid rule."""
    fpr, tpr, _ = roc_curve(y, scores)
    return float(np.sum(np.diff(fpr) * (tpr[1:] + tpr[:-1]) / 2))
