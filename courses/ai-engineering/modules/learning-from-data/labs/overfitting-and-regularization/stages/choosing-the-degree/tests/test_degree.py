import numpy as np
import pytest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from model import errors, fit, standardize


@pytest.fixture(scope="module")
def data():
    """The lab's training and validation tests, as (X_train, y_train, X_val, y_val)."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, y, X = table[:, 0], table[:, 2], table[:, 3:]
    return X[part == 0], y[part == 0], X[part == 1], y[part == 1]


def copies(data):
    return [array.copy() for array in data]


@pytest.mark.id("tst_qy6bhk")
def test_standardized(data):
    """The training set's columns have mean 0 and standard deviation 1"""
    X_train, _, X_val, _ = copies(data)
    scaled, _ = standardize(X_train, X_val)
    scaled = np.asarray(scaled, dtype=float)
    assert np.allclose(scaled.mean(axis=0), 0, atol=1e-12)
    assert np.allclose(scaled.std(axis=0), 1, atol=1e-12)


@pytest.mark.id("tst_7ld3vc")
def test_validation_scaled_like_training(data):
    """The validation set is scaled with the training set's numbers"""
    X_train, _, X_val, _ = data
    _, scaled = standardize(X_train.copy(), X_val.copy())
    expected = (X_val - X_train.mean(axis=0)) / X_train.std(axis=0)
    assert np.allclose(np.asarray(scaled, dtype=float), expected, atol=1e-12)


@pytest.mark.id("tst_q2nohz")
def test_line_through_two_points():
    """A line through two points"""
    w, b = fit(np.array([[0.0], [1.0]]), np.array([20.0, 50.0]))
    assert np.asarray(w, dtype=float) == pytest.approx([30.0])
    assert b == pytest.approx(20.0)


@pytest.mark.id("tst_lmvvp3")
def test_same_errors_as_scikit_learn(data):
    """The same errors as scikit-learn at degrees 1 to 3"""
    X_train, y_train, X_val, y_val = data
    for degree in (1, 2, 3):
        exact = make_pipeline(
            PolynomialFeatures(degree, include_bias=False),
            StandardScaler(),
            LinearRegression(),
        ).fit(X_train, y_train)
        train_rmse, val_rmse = errors(*copies(data), degree)
        expected_train = root_mean_squared_error(y_train, exact.predict(X_train))
        expected_val = root_mean_squared_error(y_val, exact.predict(X_val))
        assert train_rmse == pytest.approx(expected_train, abs=1e-6)
        assert val_rmse == pytest.approx(expected_val, abs=1e-6)


@pytest.mark.id("tst_uyh647")
def test_training_error_falls(data):
    """The training error falls at every degree, to degree 4"""
    train = [errors(*copies(data), degree)[0] for degree in (1, 2, 3, 4)]
    assert all(later < earlier for earlier, later in zip(train, train[1:]))


@pytest.mark.id("tst_e412zc")
def test_validation_error_lowest_at_two(data):
    """The validation error is lowest at degree 2"""
    val = [errors(*copies(data), degree)[1] for degree in (1, 2, 3, 4)]
    assert int(np.argmin(val)) + 1 == 2
