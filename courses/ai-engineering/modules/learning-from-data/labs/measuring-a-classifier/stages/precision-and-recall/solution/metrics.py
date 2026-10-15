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


def pr_curve(y, scores):
    """The precision and recall at each distinct score as the threshold, lowest first,
    then precision 1 at recall 0, as scikit-learn's precision_recall_curve gives them."""
    y = np.asarray(y)
    fpr, tpr, thresholds = roc_curve(y, scores)
    pulsars = np.sum(y == 1)
    found, false = tpr[1:] * pulsars, fpr[1:] * (len(y) - pulsars)
    precision = found / (found + false)
    return (
        np.append(precision[::-1], 1.0),
        np.append(tpr[1:][::-1], 0.0),
        thresholds[1:][::-1],
    )


def average_precision(y, scores):
    """Each threshold's precision, weighted by the recall it adds."""
    precision, recall, _ = pr_curve(y, scores)
    return float(np.sum((recall[:-1] - recall[1:]) * precision[:-1]))


def precision_at(share, tpr, fpr):
    """The precision of flags with these true and false positive rates, among candidates
    of which `share` are pulsars: 1 where nothing is flagged."""
    found = share * np.asarray(tpr, dtype=float)
    flagged = found + (1 - share) * np.asarray(fpr, dtype=float)
    return np.divide(found, flagged, out=np.ones_like(flagged), where=flagged > 0)
