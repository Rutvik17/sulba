import numpy as np
import pytest
from sklearn.linear_model import LinearRegression

from model import fit, predict


@pytest.fixture(scope="module")
def data():
    """The lab's training and test hours, as (X_train, y_train, X_test, y_test)."""
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    return X[~test], y[~test], X[test], y[test]


@pytest.fixture(scope="module")
def fitted(data):
    """Your weights and bias on the training hours, and scikit-learn's LinearRegression."""
    X_train, y_train, _, _ = data
    w, b = fit(X_train.copy(), y_train.copy())
    return (
        np.asarray(w, dtype=float),
        float(b),
        LinearRegression().fit(X_train, y_train),
    )


@pytest.mark.id("tst_6vzroj")
def test_two_points():
    """A line through two points"""
    w, b = fit(np.array([[0.0], [1.0]]), np.array([1.0, 3.0]))
    assert np.asarray(w, dtype=float) == pytest.approx([2.0])
    assert b == pytest.approx(1.0)


@pytest.mark.id("tst_1b698m")
def test_weights(fitted):
    """The same weights as scikit-learn"""
    w, _, exact = fitted
    assert w == pytest.approx(exact.coef_, abs=1e-8)


@pytest.mark.id("tst_xlngna")
def test_bias(fitted):
    """The same bias as scikit-learn"""
    _, b, exact = fitted
    assert b == pytest.approx(exact.intercept_, abs=1e-6)


@pytest.mark.id("tst_d3dqys")
def test_forecasts(data, fitted):
    """The same forecasts as scikit-learn on every test hour"""
    X_test = data[2]
    w, b, exact = fitted
    assert np.max(np.abs(predict(X_test, w, b) - exact.predict(X_test))) <= 1e-6


@pytest.mark.id("tst_a4eajz")
def test_repeated_column(data):
    """A column that repeats another"""
    X_train, y_train, X_test, _ = data
    twice = np.column_stack([X_train, X_train[:, 0]])
    w, b = fit(twice.copy(), y_train.copy())
    w = np.asarray(w, dtype=float)
    assert np.all(np.isfinite(w)), "the weights should be numbers"
    test = np.column_stack([X_test, X_test[:, 0]])
    exact = LinearRegression().fit(twice, y_train).predict(test)
    assert np.max(np.abs(predict(test, w, b) - exact)) <= 1e-6
