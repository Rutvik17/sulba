import numpy as np
import pytest
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import root_mean_squared_error
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from model import choose, errors, ridge

DEGREES = [1, 2, 3]
PENALTIES = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1]


@pytest.fixture(scope="module")
def data():
    """The lab's training and validation tests, as (X_train, y_train, X_val, y_val)."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, y, X = table[:, 0], table[:, 2], table[:, 3:]
    return X[part == 0], y[part == 0], X[part == 1], y[part == 1]


def copies(data):
    return [array.copy() for array in data]


@pytest.fixture(scope="module")
def scaled(data):
    """The training tests' features of degree 2, standardized by scikit-learn."""
    poly = PolynomialFeatures(2, include_bias=False)
    return StandardScaler().fit_transform(poly.fit_transform(data[0]))


@pytest.fixture(scope="module")
def chosen(data):
    """Your choice of degree and penalty, and the validation RMSE of each pair, from the
    closed form that matches scikit-learn's Ridge."""
    X_train, y_train, X_val, y_val = data
    scores = {}
    for degree in DEGREES:
        poly = PolynomialFeatures(degree, include_bias=False)
        scaler = StandardScaler()
        P_train = scaler.fit_transform(poly.fit_transform(X_train))
        P_val = scaler.transform(poly.transform(X_val))
        gram, moment = P_train.T @ P_train, P_train.T @ (y_train - y_train.mean())
        for penalty in PENALTIES:
            shrunk = gram + len(y_train) * penalty * np.eye(len(gram))
            w = np.linalg.solve(shrunk, moment)
            scores[degree, penalty] = root_mean_squared_error(
                y_val, P_val @ w + y_train.mean()
            )
    return choose(*copies(data), DEGREES, PENALTIES), scores


@pytest.mark.id("tst_r9paar")
def test_same_as_scikit_learn(data, scaled):
    """The same weights and bias as scikit-learn's Ridge"""
    y_train = data[1]
    for penalty in (1e-4, 1e-2, 1.0):
        w, b = ridge(scaled.copy(), y_train.copy(), penalty)
        exact = Ridge(alpha=len(y_train) * penalty).fit(scaled, y_train)
        assert np.asarray(w, dtype=float) == pytest.approx(exact.coef_, abs=1e-8)
        assert b == pytest.approx(exact.intercept_, abs=1e-6)


@pytest.mark.id("tst_mo2iw3")
def test_bias_not_penalized(data):
    """The bias isn't penalized, even on measurements that aren't standardized"""
    X_train, y_train = data[0], data[1]
    w, b = ridge(X_train.copy(), y_train.copy(), 0.1)
    exact = Ridge(alpha=len(y_train) * 0.1).fit(X_train, y_train)
    assert np.asarray(w, dtype=float) == pytest.approx(exact.coef_, abs=1e-8)
    assert b == pytest.approx(exact.intercept_, abs=1e-6)


@pytest.mark.id("tst_mj7nm4")
def test_no_penalty(data, scaled):
    """With no penalty, it is least squares"""
    y_train = data[1]
    w, b = ridge(scaled.copy(), y_train.copy(), 0.0)
    exact = LinearRegression().fit(scaled, y_train)
    assert np.asarray(w, dtype=float) == pytest.approx(exact.coef_, abs=1e-6)
    assert b == pytest.approx(exact.intercept_, abs=1e-6)


@pytest.mark.id("tst_xbzfm2")
def test_large_penalty(data, scaled):
    """A very large penalty leaves only the mean strength"""
    y_train = data[1]
    w, b = ridge(scaled.copy(), y_train.copy(), 1e9)
    assert np.max(np.abs(np.asarray(w, dtype=float))) < 1e-6
    assert b == pytest.approx(y_train.mean(), abs=1e-6)


@pytest.mark.id("tst_mj57yr")
def test_choose(chosen):
    """Chooses the degree and penalty with the lowest validation RMSE"""
    (degree, penalty, val_rmse), scores = chosen
    best = min(scores, key=scores.get)
    assert (degree, penalty) == best
    assert val_rmse == pytest.approx(scores[best], abs=1e-6)


@pytest.mark.id("tst_e0768t")
def test_beats_least_squares(data, chosen):
    """The chosen model beats least squares at degree 2 on the validation mixes"""
    (_, _, val_rmse), _ = chosen
    assert val_rmse < errors(*copies(data), 2)[1]
