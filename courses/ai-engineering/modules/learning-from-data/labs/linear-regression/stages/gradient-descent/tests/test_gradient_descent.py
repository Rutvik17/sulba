import numpy as np
import pytest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from model import gradient, standardize, train


@pytest.fixture(scope="module")
def data():
    """The lab's training and test hours, as (X_train, y_train, X_test, y_test)."""
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    return X[~test], y[~test], X[test], y[test]


@pytest.fixture(scope="module")
def scaled(data):
    """Both sets standardized with the training set's numbers."""
    X_train, _, X_test, _ = data
    scaler = StandardScaler().fit(X_train)
    return scaler.transform(X_train), scaler.transform(X_test)


@pytest.mark.id("tst_5f2sli")
def test_mean_zero(data):
    """Training columns have mean 0"""
    X_train, _, X_test, _ = data
    scaled, _ = standardize(X_train.copy(), X_test.copy())
    assert np.max(np.abs(scaled.mean(axis=0))) <= 1e-9


@pytest.mark.id("tst_y3tj86")
def test_deviation_one(data):
    """Training columns have standard deviation 1"""
    X_train, _, X_test, _ = data
    scaled, _ = standardize(X_train.copy(), X_test.copy())
    assert np.max(np.abs(scaled.std(axis=0) - 1)) <= 1e-9


@pytest.mark.id("tst_thncpb")
def test_test_set_uses_training_numbers(data, scaled):
    """The test set uses the training set's means and standard deviations"""
    X_train, _, X_test, _ = data
    _, yours = standardize(X_train.copy(), X_test.copy())
    assert np.max(np.abs(yours - scaled[1])) <= 1e-9


@pytest.mark.id("tst_nggb2p")
def test_gradient(scaled, data):
    """The gradient matches a numerical estimate"""
    X, y = scaled[0][:200], data[1][:200]
    w, b = np.array([1.0, -2.0, 0.5, 3.0]), 400.0

    def loss(w, b):
        return np.mean((X @ w + b - y) ** 2)

    dw, db = gradient(X, y, w, b)
    h = 1e-5
    numeric = [
        (loss(w + h * step, b) - loss(w - h * step, b)) / (2 * h)
        for step in np.eye(len(w))
    ]
    assert np.asarray(dw, dtype=float) == pytest.approx(numeric, rel=1e-6)
    assert db == pytest.approx((loss(w, b + h) - loss(w, b - h)) / (2 * h), rel=1e-6)


@pytest.mark.id("tst_k6xk2n")
def test_starting_point(scaled, data):
    """Starts from zero weights and the mean output"""
    w, b, losses = train(scaled[0], data[1], steps=0)
    assert np.asarray(w, dtype=float) == pytest.approx(np.zeros(4))
    assert b == pytest.approx(np.mean(data[1]))
    assert len(losses) == 0


@pytest.mark.id("tst_zkjpgw")
def test_each_step_lowers_the_loss(scaled, data):
    """Each step lowers the loss"""
    _, _, losses = train(scaled[0], data[1], steps=200)
    assert len(losses) == 200
    assert np.all(np.diff(losses) <= 1e-12), "a step raised the loss"


@pytest.mark.id("tst_fsps2a")
def test_matches_least_squares(scaled, data):
    """Matches least squares on every test hour"""
    X_train, X_test = scaled
    w, b, _ = train(X_train, data[1])
    exact = LinearRegression().fit(X_train, data[1]).predict(X_test)
    assert np.max(np.abs(X_test @ np.asarray(w, dtype=float) + b - exact)) <= 0.01
