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
    # Pulsars are rare, so the classes are balanced: each counts as much as the other.
    return make_pipeline(
        StandardScaler(), LogisticRegression(class_weight="balanced")
    ).fit(X, y)


def measured_on(X, y):
    """The candidates to measure the classifier on."""
    # As many other candidates as pulsars, so the others don't swamp the measures.
    rng = np.random.default_rng(0)
    pulsars = np.flatnonzero(y == 1)
    others = rng.choice(np.flatnonzero(y == 0), len(pulsars), replace=False)
    rows = np.sort(np.concatenate([pulsars, others]))
    return X[rows], y[rows]


def auc(model, X, y):
    """The classifier's ROC AUC on these candidates."""
    return float(roc_auc_score(y, model.predict(X)))


def precision(model, X, y):
    """The share of pulsars among the candidates flagged at the threshold."""
    flagged = model.predict_proba(X)[:, 1] >= THRESHOLD
    return float(y[flagged].mean())


def expected_pulsars(p):
    """How many pulsars to expect among candidates with these probabilities."""
    return int((p >= THRESHOLD).sum())


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
