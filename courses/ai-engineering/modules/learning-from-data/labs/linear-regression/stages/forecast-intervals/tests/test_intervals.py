import numpy as np
import pytest

from forecaster import COLUMNS, Forecaster, halfwidth, intervals


def rank(n, coverage):
    return int(np.ceil((n + 1) * coverage))


@pytest.mark.id("tst_jc0lm4")
def test_rank():
    """The rank of the miss that sets the width"""
    misses = np.array([9.0, 2.0, 7.0, 1.0, 5.0, 3.0, 8.0, 4.0, 6.0])
    assert halfwidth(misses.copy(), 0.8) == pytest.approx(rank(9, 0.8))


@pytest.mark.id("tst_uspcjb")
def test_sizes():
    """A miss below the forecast counts by its size"""
    misses = np.array([-5.0, 1.0, -2.0, 4.0, -3.0])
    assert halfwidth(misses.copy(), 0.5) == pytest.approx(3.0)


@pytest.mark.id("tst_73ly10")
def test_too_few():
    """Too few misses for the coverage asked"""
    assert halfwidth(np.array([1.0, 2.0, 3.0, 4.0, 5.0]), 0.9) == float("inf")


@pytest.mark.id("tst_n354nt")
def test_around_each_forecast():
    """An interval around each forecast"""
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    train = table[table[:, 0] == 0]
    forecaster = Forecaster().fit(train[:, 2:], train[:, 1])
    weather = {name: train[:24, 2 + column] for column, name in enumerate(COLUMNS)}
    low, high = intervals(forecaster, weather, 7.5)
    forecasts = forecaster.forecast(weather)
    assert np.asarray(low, dtype=float) == pytest.approx(forecasts - 7.5)
    assert np.asarray(high, dtype=float) == pytest.approx(forecasts + 7.5)
