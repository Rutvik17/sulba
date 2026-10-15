import numpy as np
import pytest

from forecaster import COLUMNS, Forecaster


@pytest.fixture(scope="module")
def history():
    """The plant's history: the lab's training hours."""
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    train = table[table[:, 0] == 0]
    return train[:, 2:], train[:, 1]


def a_day(history):
    """24 hours of weather from the history, as the weather service sends it."""
    X = history[0][:24]
    return {name: X[:, column] for column, name in enumerate(COLUMNS)}


@pytest.mark.id("tst_6dk7a0")
def test_a_forecast_per_hour(history):
    """A forecast for each hour of a day"""
    forecaster = Forecaster().fit(*history)
    assert len(forecaster.forecast(a_day(history))) == 24


@pytest.mark.id("tst_i6mkrk")
def test_a_weight_per_measurement(history):
    """A weight for each weather measurement"""
    forecaster = Forecaster().fit(*history)
    assert forecaster.model.coef_.shape == (len(COLUMNS),)


@pytest.mark.id("tst_wpq3rk")
def test_numbers(history):
    """Forecasts are numbers"""
    forecaster = Forecaster().fit(*history)
    assert np.all(np.isfinite(forecaster.forecast(a_day(history))))
