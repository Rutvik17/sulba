import numpy as np
import pytest

from forecaster import COLUMNS, Forecaster
from model import fit


@pytest.fixture(scope="module")
def data():
    """The lab's training and test hours, as (X_train, y_train, X_test, y_test)."""
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    return X[~test], y[~test], X[test], y[test]


@pytest.fixture(scope="module")
def forecaster(data):
    """A forecaster fitted once on the history, as the plant will fit it."""
    return Forecaster().fit(data[0].copy(), data[1].copy())


def weather(X):
    """Hours of weather as the weather service sends them: each measurement by name."""
    return {name: X[:, column].copy() for column, name in enumerate(COLUMNS)}


@pytest.mark.id("tst_qjj1l0")
def test_same_forecasts(data, forecaster):
    """The same forecasts as the model you validated"""
    X_train, y_train, X_test, _ = data
    w, b = fit(X_train.copy(), y_train.copy())
    yours = X_test @ np.asarray(w, dtype=float) + b
    # Hours your model forecasts inside the range of outputs in the history.
    usual = (yours > y_train.min()) & (yours < y_train.max())
    forecasts = np.asarray(forecaster.forecast(weather(X_test[usual])), dtype=float)
    assert forecasts.shape == yours[usual].shape
    assert np.max(np.abs(forecasts - yours[usual])) <= 1e-6


@pytest.mark.id("tst_j4u8zv")
def test_missing_weather(data, forecaster):
    """Names the hours that have no weather, and forecasts none of them"""
    day = weather(data[2][:24])
    day["temperature"][5] = np.nan
    with pytest.raises(ValueError, match="5"):
        forecaster.forecast(day)


@pytest.mark.id("tst_si8a2y")
def test_beyond_the_history(data, forecaster):
    """Weather beyond the history still moves the forecast"""
    # Two hours colder than any in the history, with ordinary vacuum, pressure and humidity.
    cold = {
        "temperature": np.array([-5.0, -10.0]),
        "vacuum": np.array([40.0, 40.0]),
        "pressure": np.array([1015.0, 1015.0]),
        "humidity": np.array([70.0, 70.0]),
    }
    forecasts = np.asarray(forecaster.forecast(cold), dtype=float)
    assert forecasts.shape == (2,)
    assert forecasts[0] != forecasts[1]


@pytest.mark.id("tst_jqdzkb")
def test_one_hour(data, forecaster):
    """One hour at a time"""
    hour = {name: float(data[2][0, column]) for column, name in enumerate(COLUMNS)}
    forecasts = np.asarray(forecaster.forecast(hour), dtype=float).reshape(-1)
    assert forecasts.shape == (1,)
    assert np.isfinite(forecasts[0])
