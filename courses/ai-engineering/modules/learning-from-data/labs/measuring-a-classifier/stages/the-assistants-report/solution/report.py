"""The survey's report on its pulsar classifier."""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

THRESHOLD = 0.5


def candidates(table, part):
    """The measurements and labels of the candidates in one set: 0 for training, 1 for
    validation and 2 for test."""
    rows = table[:, 0] == part
    return table[rows, 2:], table[rows, 1]


def trained(X, y):
    """The survey's classifier, fit on these candidates."""
    return make_pipeline(StandardScaler(), LogisticRegression()).fit(X, y)


def measured_on(X, y):
    """The candidates to measure the classifier on."""
    return X, y


def auc(model, X, y):
    """The classifier's ROC AUC on these candidates."""
    return float(roc_auc_score(y, model.predict_proba(X)[:, 1]))


def precision(model, X, y):
    """The share of pulsars among the candidates flagged at the threshold."""
    flagged = model.predict_proba(X)[:, 1] >= THRESHOLD
    return float(y[flagged].mean())


def expected_pulsars(p):
    """How many pulsars to expect among candidates with these probabilities."""
    return float(np.sum(p))


def report(table):
    """What the survey asked for: the classifier's AUC and precision on the test set,
    and the pulsars to expect among its candidates."""
    model = trained(*candidates(table, 0))
    X, y = candidates(table, 2)
    measured = measured_on(X, y)
    return {
        "auc": auc(model, *measured),
        "precision": precision(model, *measured),
        "expected": expected_pulsars(model.predict_proba(X)[:, 1]),
    }
