import numpy as np
import pytest
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from metrics import brier, reliability


@pytest.fixture(scope="module")
def survey():
    """The test set's labels, and the survey classifier's probabilities for them."""
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    model = make_pipeline(StandardScaler(), LogisticRegression())
    model.fit(table[train, 2:], table[train, 1])
    return table[test, 1], model.predict_proba(table[test, 2:])[:, 1]


def table_of(y, p, bins):
    return tuple(np.asarray(part, dtype=float) for part in reliability(y, p, bins))


def same(found, expected):
    for part, exact in zip(found, expected, strict=True):
        assert part.shape == exact.shape
        assert np.allclose(part, exact, rtol=0, atol=1e-12)


@pytest.mark.id("tst_1cuwn1")
def test_small_case():
    """Five candidates in five bins, worked by hand"""
    y = np.array([0, 1, 0, 1, 1])
    p = np.array([0.05, 0.15, 0.55, 0.6, 0.95])
    share, mean = table_of(y, p, 5)
    assert np.allclose(share, [0.5, 0.5, 1], rtol=0, atol=1e-12)
    assert np.allclose(mean, [0.1, 0.575, 0.95], rtol=0, atol=1e-12)


@pytest.mark.id("tst_8mf8nx")
def test_same_as_scikit_learn(survey):
    """The same table as scikit-learn's, in 5, 10 and 20 bins"""
    y, p = survey
    for bins in (5, 10, 20):
        same(table_of(y.copy(), p.copy(), bins), calibration_curve(y, p, n_bins=bins))


@pytest.mark.id("tst_0x0eme")
def test_edges_go_to_the_bin_below():
    """A probability on an edge goes in the bin below it, and 0 in the first"""
    y = np.array([0, 1, 0, 1, 0, 1, 1])
    p = np.array([0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0])
    for bins in (5, 10):
        same(table_of(y, p, bins), calibration_curve(y, p, n_bins=bins))


@pytest.mark.id("tst_ojyxa4")
def test_empty_bins_left_out():
    """Bins with no probabilities are left out"""
    share, mean = table_of(np.array([0, 1, 0]), np.array([0.02, 0.05, 0.08]), 10)
    assert share.shape == mean.shape == (1,)
    assert mean[0] == pytest.approx(0.05)


@pytest.mark.id("tst_84zsdo")
def test_same_brier_score_as_scikit_learn(survey):
    """The same Brier score as scikit-learn's"""
    y, p = survey
    assert brier(y.copy(), p.copy()) == pytest.approx(
        brier_score_loss(y, p), rel=0, abs=1e-12
    )
    assert brier(np.array([0, 1]), np.array([0.0, 1.0])) == 0
    assert brier(np.array([0, 1]), np.array([1.0, 0.0])) == 1
