import numpy as np
import pytest

from forecaster import COLUMNS, Forecaster, halfwidth, intervals

COVERAGE = 0.9
WIDEST_MW = 15.0


def weather(X):
    """Hours of weather as the weather service sends them: each measurement by name."""
    return {name: X[:, column].copy() for column, name in enumerate(COLUMNS)}


@pytest.fixture(scope="module")
def calibrated():
    """A forecaster fitted on four of every five training hours, the half-width from its
    misses on the fifth, and the test hours."""
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, y_train = X[~test], y[~test]
    held = np.arange(len(y_train)) % 5 == 0
    forecaster = Forecaster().fit(X_train[~held], y_train[~held])
    misses = y_train[held] - forecaster.forecast(weather(X_train[held]))
    return forecaster, halfwidth(misses, COVERAGE), X[test], y[test]


@pytest.mark.id("tst_dfk68y")
def test_coverage(calibrated, record_property):
    """Covers at least 90% of new hours"""
    forecaster, q, X_test, y_test = calibrated
    low, high = intervals(forecaster, weather(X_test), q)
    inside = float(np.mean((y_test >= np.asarray(low)) & (y_test <= np.asarray(high))))
    record_property("note", f"{inside:.1%} of the test hours inside")
    assert inside >= COVERAGE


@pytest.mark.id("tst_fjzvod")
def test_width(calibrated, record_property):
    """No more than 15 MW wide"""
    q = calibrated[1]
    record_property("note", f"{2 * q:.1f} MW wide")
    assert 2 * q <= WIDEST_MW


@pytest.mark.id("tst_4a0lxi")
def test_one_hour(calibrated):
    """One hour at a time"""
    forecaster, q, X_test, _ = calibrated
    hour = {name: float(X_test[0, column]) for column, name in enumerate(COLUMNS)}
    low, high = intervals(forecaster, hour, q)
    assert np.asarray(low, dtype=float).reshape(-1).shape == (1,)
    assert np.asarray(high, dtype=float).reshape(-1).shape == (1,)
