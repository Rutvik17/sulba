import numpy as np
import pytest
from sklearn import metrics as reference
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from metrics import roc_auc, roc_curve


@pytest.fixture(scope="module")
def survey():
    """The test set's labels, and the survey classifier's probabilities for them."""
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    model = make_pipeline(StandardScaler(), LogisticRegression())
    model.fit(table[train, 2:], table[train, 1])
    return table[test, 1], model.predict_proba(table[test, 2:])[:, 1]


def curve(y, scores):
    return tuple(np.asarray(part, dtype=float) for part in roc_curve(y, scores))


@pytest.mark.id("tst_r706zt")
def test_small_case():
    """Four candidates, worked by hand"""
    fpr, tpr, thresholds = curve(
        np.array([0, 0, 1, 1]), np.array([0.1, 0.4, 0.35, 0.8])
    )
    assert fpr.tolist() == [0, 0, 0.5, 0.5, 1]
    assert tpr.tolist() == [0, 0.5, 0.5, 1, 1]
    assert thresholds.tolist() == [np.inf, 0.8, 0.4, 0.35, 0.1]


@pytest.mark.id("tst_981mao")
def test_from_nothing_flagged_to_everything(survey):
    """Starts where nothing is flagged and ends where everything is"""
    fpr, tpr, thresholds = curve(*survey)
    assert thresholds[0] == np.inf
    assert (fpr[0], tpr[0]) == (0, 0)
    assert (fpr[-1], tpr[-1]) == (1, 1)


@pytest.mark.id("tst_4or0kt")
def test_same_curve_as_scikit_learn(survey):
    """The same curve as scikit-learn's"""
    y, scores = survey
    found = curve(y.copy(), scores.copy())
    expected = reference.roc_curve(y, scores, drop_intermediate=False)
    for part, exact in zip(found, expected, strict=True):
        assert part.shape == exact.shape
        assert np.allclose(part, exact, rtol=0, atol=1e-12)


@pytest.mark.id("tst_a4l941")
def test_ties_cross_together(survey):
    """Candidates with the same score cross the threshold together"""
    y, scores = survey
    rounded = np.round(scores, 2)
    found = curve(y, rounded)
    expected = reference.roc_curve(y, rounded, drop_intermediate=False)
    for part, exact in zip(found, expected, strict=True):
        assert part.shape == exact.shape
        assert np.allclose(part, exact, rtol=0, atol=1e-12)


@pytest.mark.id("tst_w0wahg")
def test_same_auc_as_scikit_learn(survey):
    """The same AUC as scikit-learn's, with and without ties"""
    y, scores = survey
    for given in (scores, np.round(scores, 2), np.round(scores, 1)):
        expected = reference.roc_auc_score(y, given)
        assert roc_auc(y, given.copy()) == pytest.approx(expected, rel=0, abs=1e-12)


@pytest.mark.id("tst_0jgr9a")
def test_only_the_order_counts(survey):
    """Only the scores' order counts: log-odds give the same AUC, reversed scores 1 - AUC"""
    y, scores = survey
    auc = roc_auc(y, scores)
    log_odds = np.log(scores) - np.log1p(-scores)
    assert roc_auc(y, log_odds) == pytest.approx(auc, rel=0, abs=1e-12)
    assert roc_auc(y, -scores) == pytest.approx(1 - auc, rel=0, abs=1e-12)
