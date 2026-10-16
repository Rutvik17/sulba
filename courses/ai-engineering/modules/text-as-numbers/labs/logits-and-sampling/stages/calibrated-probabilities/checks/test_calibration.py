import numpy as np
import pytest
from scipy.optimize import minimize
from scipy.special import expit, log_expit

from judge import calibrate, load_pairs, match_probability

# How far above the least log loss on the validation pairs a fit may come.
TOLERANCE = 0.001


@pytest.fixture(scope="module")
def fitted():
    """The validation and test pairs, and the temperature and shift fitted on the
    first."""
    pairs, _, _ = load_pairs()
    validation = pairs[pairs["set"] == "validation"]
    test = pairs[pairs["set"] == "test"]
    return validation, test, calibrate(validation)


def margin(pairs):
    return (pairs["yes"] - pairs["no"]).to_numpy()


def exact(pairs):
    return (pairs["label"] == "E").to_numpy()


def log_loss(pairs, slope, shift):
    scores = margin(pairs) * slope + shift
    return -np.mean(np.where(exact(pairs), log_expit(scores), log_expit(-scores)))


@pytest.mark.id("tst_eut4u5")
def test_probability():
    """The judge's own probability, scaled and shifted"""
    pairs, _, _ = load_pairs()
    for temperature, shift in [(1.0, 0.0), (6.9, -0.42), (0.5, 1.5)]:
        found = match_probability(pairs, temperature, shift)
        wanted = expit(margin(pairs) / temperature + shift)
        np.testing.assert_allclose(found, wanted, rtol=1e-9)


@pytest.mark.id("tst_wsc48h")
def test_fitted(fitted):
    """Fitted to the validation pairs"""
    validation, _, (temperature, shift) = fitted
    least = minimize(lambda fit: log_loss(validation, *fit), x0=[1.0, 0.0])
    assert temperature > 0
    assert log_loss(validation, 1 / temperature, shift) <= least.fun + TOLERANCE


@pytest.mark.id("tst_pe0ikj")
def test_brier(fitted):
    """Better than one share for every pair"""
    validation, test, (temperature, shift) = fitted
    probabilities = expit(margin(test) / temperature + shift)
    share = exact(validation).mean()
    brier = np.mean((probabilities - exact(test)) ** 2)
    assert brier < np.mean((share - exact(test)) ** 2)


@pytest.mark.id("tst_kc9h17")
def test_adds_up(fitted):
    """Probabilities that add up"""
    _, test, (temperature, shift) = fitted
    probabilities = expit(margin(test) / temperature + shift)
    spread = np.sqrt(np.sum(probabilities * (1 - probabilities)))
    assert abs(probabilities.sum() - exact(test).sum()) <= 2 * spread
