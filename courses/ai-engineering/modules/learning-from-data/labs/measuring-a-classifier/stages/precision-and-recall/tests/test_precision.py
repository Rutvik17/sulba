import numpy as np
import pytest
from sklearn import metrics as reference
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from metrics import average_precision, pr_curve, precision_at


@pytest.fixture(scope="module")
def survey():
    """The test set's labels, and the survey classifier's probabilities for them."""
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    model = make_pipeline(StandardScaler(), LogisticRegression())
    model.fit(table[train, 2:], table[train, 1])
    return table[test, 1], model.predict_proba(table[test, 2:])[:, 1]


def curve(y, scores):
    return tuple(np.asarray(part, dtype=float) for part in pr_curve(y, scores))


def same(found, expected):
    for part, exact in zip(found, expected, strict=True):
        assert part.shape == exact.shape
        assert np.allclose(part, exact, rtol=0, atol=1e-12)


@pytest.mark.id("tst_17pldn")
def test_small_case():
    """Four candidates, worked by hand"""
    y, scores = np.array([0, 0, 1, 1]), np.array([0.1, 0.4, 0.35, 0.8])
    precision, recall, thresholds = curve(y, scores)
    assert np.allclose(precision, [0.5, 2 / 3, 0.5, 1, 1], rtol=0, atol=1e-12)
    assert recall.tolist() == [1, 1, 0.5, 0.5, 0]
    assert thresholds.tolist() == [0.1, 0.35, 0.4, 0.8]
    assert average_precision(y, scores) == pytest.approx(5 / 6, rel=0, abs=1e-12)


@pytest.mark.id("tst_ns4bwj")
def test_same_curve_as_scikit_learn(survey):
    """The same curve as scikit-learn's, with and without ties"""
    y, scores = survey
    for given in (scores, np.round(scores, 2)):
        same(curve(y.copy(), given.copy()), reference.precision_recall_curve(y, given))


@pytest.mark.id("tst_fo4p34")
def test_same_average_precision_as_scikit_learn(survey):
    """The same average precision as scikit-learn's, with and without ties"""
    y, scores = survey
    for given in (scores, np.round(scores, 2), np.round(scores, 1)):
        expected = reference.average_precision_score(y, given)
        found = average_precision(y.copy(), given.copy())
        assert found == pytest.approx(expected, rel=0, abs=1e-12)


@pytest.mark.id("tst_d2952t")
def test_precision_at_the_test_sets_share(survey):
    """At the test set's own share of pulsars, the precision of its flags"""
    y, scores = survey
    fpr, tpr, thresholds = reference.roc_curve(y, scores, drop_intermediate=False)
    found = np.asarray(precision_at(y.mean(), tpr[1:], fpr[1:]), dtype=float)
    flagged = scores[None, :] >= thresholds[1:, None]
    expected = (flagged & (y == 1)).sum(axis=1) / flagged.sum(axis=1)
    assert np.allclose(found, expected, rtol=0, atol=1e-12)


@pytest.mark.id("tst_517nin")
def test_precision_at_other_shares(survey):
    """At another share, the precision scikit-learn gives with the classes weighted to it"""
    y, scores = survey
    fpr, tpr, _ = reference.roc_curve(y, scores, drop_intermediate=False)
    for share in (0.001, 0.01, 0.5):
        weight = np.where(y == 1, share / y.mean(), (1 - share) / (1 - y.mean()))
        expected, _, _ = reference.precision_recall_curve(
            y, scores, sample_weight=weight
        )
        found = np.asarray(precision_at(share, tpr[1:], fpr[1:]), dtype=float)
        assert np.allclose(found[::-1], expected[:-1], rtol=0, atol=1e-9)


@pytest.mark.id("tst_0ewnto")
def test_precision_at_one_threshold():
    """One threshold's rates give one precision, and nothing flagged gives 1"""
    assert float(precision_at(0.1, 0.8, 0.02)) == pytest.approx(0.08 / (0.08 + 0.018))
    assert float(precision_at(0.1, 0.0, 0.0)) == 1
