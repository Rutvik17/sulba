import numpy as np
import pytest
from scipy.stats import t

from compare import corrected_se, interval

# Differences on 25 folds, drawn once, and the folds' calls fitted on and held out.
DIFFERENCES = np.random.default_rng(0).normal(0.005, 0.012, 25)
N_FIT, N_HELD = 3294, 824


def reference_se(differences, n_train, n_test):
    """The corrected standard deviation of scikit-learn's guide to comparing models."""
    kr = len(differences)
    return np.sqrt(np.var(differences, ddof=1) * (1 / kr + n_test / n_train))


@pytest.mark.id("tst_nfagin")
def test_by_hand():
    """A standard error by hand"""
    found = corrected_se(np.array([0.01, 0.03, 0.02, 0.04]), 300, 100)
    assert found == pytest.approx(np.sqrt(0.0005 / 3 * (1 / 4 + 1 / 3)), rel=1e-12)


@pytest.mark.id("tst_av8sfa")
def test_reference():
    """The corrected standard error of 25 folds"""
    found = corrected_se(DIFFERENCES, N_FIT, N_HELD)
    assert found == pytest.approx(reference_se(DIFFERENCES, N_FIT, N_HELD), rel=1e-12)


@pytest.mark.id("tst_3vpuut")
def test_interval():
    """Intervals at 95% and 99% from the t distribution"""
    mean = DIFFERENCES.mean()
    se = reference_se(DIFFERENCES, N_FIT, N_HELD)
    for confidence in [0.95, 0.99]:
        low, high = interval(DIFFERENCES, N_FIT, N_HELD, confidence)
        half = t.ppf((1 + confidence) / 2, len(DIFFERENCES) - 1) * se
        assert low == pytest.approx(mean - half, rel=1e-12)
        assert high == pytest.approx(mean + half, rel=1e-12)


@pytest.mark.id("tst_djr8sl")
def test_no_spread():
    """Differences that never vary"""
    same = np.full(25, 0.01)
    assert corrected_se(same, N_FIT, N_HELD) == pytest.approx(0, abs=1e-15)
    assert interval(same, N_FIT, N_HELD, 0.95) == pytest.approx((0.01, 0.01))
