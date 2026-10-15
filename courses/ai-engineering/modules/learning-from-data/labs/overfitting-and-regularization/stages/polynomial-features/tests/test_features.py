import numpy as np
import pytest
from sklearn.preprocessing import PolynomialFeatures

from model import features, rmse


@pytest.fixture(scope="module")
def X():
    """The measurements of every test of every mix in the lab's data."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    return table[:, 3:]


@pytest.mark.id("tst_cg7xrp")
def test_two_measurements():
    """Two measurements to degree 2"""
    P = features(np.array([[2.0, 3.0]]), 2)
    assert np.asarray(P, dtype=float).tolist() == [[2.0, 3.0, 4.0, 6.0, 9.0]]


@pytest.mark.id("tst_gn2kaf")
def test_degree_one(X):
    """Degree 1 is the measurements themselves"""
    assert np.array_equal(np.asarray(features(X.copy(), 1), dtype=float), X)


@pytest.mark.id("tst_zgprcx")
def test_same_as_scikit_learn(X):
    """The same products as scikit-learn, in the same order"""
    for degree in (2, 3):
        exact = PolynomialFeatures(degree, include_bias=False).fit_transform(X)
        P = np.asarray(features(X.copy(), degree), dtype=float)
        assert P.shape == exact.shape
        assert np.allclose(P, exact, rtol=1e-12, atol=0)


@pytest.mark.id("tst_lk4hrc")
def test_feature_count(X):
    """494 features of eight measurements at degree 4"""
    assert np.shape(features(X[:5], 4)) == (5, 494)


@pytest.mark.id("tst_86cs01")
def test_one_test(X):
    """One test at a time"""
    exact = PolynomialFeatures(2, include_bias=False).fit_transform(X[:1])
    assert np.allclose(np.asarray(features(X[:1], 2), dtype=float), exact, rtol=1e-12)


@pytest.mark.id("tst_e7r6d3")
def test_root_mean_squared_error():
    """Root mean squared error"""
    assert rmse(np.array([30.0, 40.0]), np.array([33.0, 36.0])) == pytest.approx(
        np.sqrt(12.5)
    )


@pytest.mark.id("tst_8l20m6")
def test_perfect_prediction():
    """A perfect prediction has no error"""
    y = np.array([79.99, 61.89, 40.27])
    assert rmse(y, y.copy()) == 0
