import numpy as np
import pytest

from model import mse, predict


@pytest.fixture(scope="module")
def data():
    """The lab's training and test hours, as (X_train, y_train, X_test, y_test)."""
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    return X[~test], y[~test], X[test], y[test]


@pytest.mark.id("tst_qpx5gc")
def test_three_hours():
    """Three hours"""
    X = np.array([[10.0, 40.0], [20.0, 50.0], [30.0, 60.0]])
    w = np.array([-2.0, 0.5])
    assert predict(X, w, 450.0) == pytest.approx([450.0, 435.0, 420.0])


@pytest.mark.id("tst_b2141k")
def test_one_forecast_per_hour(data):
    """One forecast per hour"""
    X_train = data[0]
    y_hat = predict(X_train, np.zeros(X_train.shape[1]), 454.0)
    assert np.shape(y_hat) == (len(X_train),)
    assert y_hat == pytest.approx(np.full(len(X_train), 454.0))


@pytest.mark.id("tst_k44nmh")
def test_mean_squared_error():
    """Mean squared error"""
    assert mse(np.array([450.0, 460.0, 470.0]), np.array([452.0, 457.0, 470.0])) == (
        pytest.approx(13 / 3)
    )


@pytest.mark.id("tst_ir84ot")
def test_perfect_forecast():
    """A perfect forecast has no error"""
    y = np.array([463.26, 444.37, 488.56])
    assert mse(y, y.copy()) == 0


@pytest.mark.id("tst_mpe0hx")
def test_forecasting_the_mean(data):
    """Forecasting the training mean for every test hour"""
    _, y_train, X_test, y_test = data
    y_hat = predict(X_test, np.zeros(X_test.shape[1]), y_train.mean())
    assert mse(y_test, y_hat) == pytest.approx(np.mean((y_test - y_train.mean()) ** 2))
