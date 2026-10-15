import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import report
from metrics import roc_auc


@pytest.fixture(scope="module")
def survey():
    """The survey's table, its classifier fit on the training set, and the test set."""
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    model = make_pipeline(StandardScaler(), LogisticRegression())
    model.fit(table[train, 2:], table[train, 1])
    return table, model, table[test, 2:], table[test, 1]


@pytest.mark.id("tst_2ydpjs")
def test_probabilities_add_up(survey):
    """Its probabilities for the test set add up to within 5% of the pulsars there"""
    table, _, X, y = survey
    model = report.trained(*report.candidates(table.copy(), 0))
    total = float(np.sum(model.predict_proba(X)[:, 1]))
    assert abs(total - y.sum()) <= 0.05 * y.sum()


@pytest.mark.id("tst_1morqj")
def test_precision_as_a_night_gives_it(survey):
    """Its precision is the test set's, with the test set's share of pulsars"""
    _, model, X, y = survey
    measured = report.measured_on(X.copy(), y.copy())
    flagged = model.predict_proba(X)[:, 1] >= report.THRESHOLD
    expected = y[flagged].mean()
    assert report.precision(model, *measured) == pytest.approx(expected, abs=1e-12)


@pytest.mark.id("tst_sxf6sq")
def test_auc_ranks_by_probability(survey):
    """Its AUC is your roc_auc of the classifier's probabilities"""
    _, model, X, y = survey
    expected = roc_auc(y, model.predict_proba(X)[:, 1])
    assert report.auc(model, X.copy(), y.copy()) == pytest.approx(expected, abs=1e-12)


@pytest.mark.id("tst_sqhljg")
def test_expected_pulsars_add_up(survey):
    """The pulsars to expect are the probabilities added up"""
    _, model, X, _ = survey
    p = model.predict_proba(X)[:, 1]
    assert report.expected_pulsars(p.copy()) == pytest.approx(p.sum(), abs=1e-9)
