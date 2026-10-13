import numpy as np
import pytest

from screener import Screener


@pytest.fixture(scope="module")
def data():
    """The lab's training and test sets, as (X_train, y_train, X_test, y_test)."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    return X[~test], y[~test], X[test], y[test]


@pytest.fixture(scope="module")
def screener(data):
    X_train, y_train, _, _ = data
    return Screener().fit(X_train.copy(), y_train.copy())


def fitted_model(screener):
    """The screener's fitted logistic regression: an attribute, or a pipeline's last step."""
    for value in vars(screener).values():
        if hasattr(value, "steps"):
            value = value.steps[-1][1]
        if hasattr(value, "coef_") and hasattr(value, "intercept_"):
            return value
    raise AttributeError("the screener keeps no fitted LogisticRegression")


@pytest.mark.id("tst_jgm8ux")
def test_one_probability_per_sample(data, screener):
    """One probability per sample"""
    X_test = data[2]
    p = np.asarray(screener.score(X_test.copy()), dtype=float).reshape(-1)
    assert len(p) == len(X_test)


@pytest.mark.id("tst_gm457v")
def test_between_zero_and_one(data, screener):
    """Every probability is between 0 and 1"""
    p = np.asarray(screener.score(data[2].copy()), dtype=float).reshape(-1)
    assert np.all((p >= 0) & (p <= 1))


@pytest.mark.id("tst_n25mrh")
def test_accuracy(data, screener):
    """The model is at least 90% accurate on the test set"""
    X_train, _, X_test, y_test = data
    scaled = (X_test - X_train.mean(axis=0)) / X_train.std(axis=0)
    assert np.mean(fitted_model(screener).predict(scaled) == y_test) >= 0.9
