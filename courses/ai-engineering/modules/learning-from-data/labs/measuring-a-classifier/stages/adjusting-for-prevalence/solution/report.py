"""The survey's report on its pulsar classifier."""

import numpy as np
from scipy.special import expit
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


class Screen:
    """The survey's classifier, fit on these candidates, with probabilities for
    candidates of which `share` are pulsars."""

    def __init__(self, X, y, share):
        """Fits the survey's classifier on these candidates with `trained`."""
        self.model = trained(X, y)
        fitted_share = float(np.mean(y))
        # Bayes' rule: the odds of a pulsar scale by the new share's odds over the old's.
        self.shift = np.log(share / (1 - share)) - np.log(
            fitted_share / (1 - fitted_share)
        )

    def probabilities(self, X):
        """Each candidate's probability of being a pulsar, where `share` of the
        candidates are."""
        return expit(self.model.decision_function(X) + self.shift)

    def follow_ups(self, X, budget):
        """The row numbers of the `budget` candidates most likely to be pulsars, most
        likely first."""
        return np.argsort(-self.probabilities(X), kind="stable")[:budget]
