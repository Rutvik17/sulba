import numpy as np
import pytest

from model import predict_proba, train
from screener import Screener


@pytest.fixture(scope="module")
def data():
    """The lab's training and test sets, as (X_train, y_train, X_test, y_test)."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    return X[~test], y[~test], X[test], y[test]


@pytest.fixture(scope="module")
def scaled(data):
    """Both sets scaled with the training set's means and standard deviations."""
    X_train, _, X_test, _ = data
    mean, std = X_train.mean(axis=0), X_train.std(axis=0)
    return (X_train - mean) / std, (X_test - mean) / std


@pytest.fixture(scope="module")
def yours(data, scaled):
    """The test set's probabilities from your model.py, trained as in stage 3."""
    y_train = data[1]
    X_train_scaled, X_test_scaled = scaled
    w, b, _ = train(X_train_scaled, y_train.copy(), l2=1 / len(y_train))
    return np.asarray(predict_proba(X_test_scaled, w, b), dtype=float).reshape(-1)


@pytest.fixture(scope="module")
def screener(data):
    """A screener fitted once on the training set, as the clinic will fit it."""
    X_train, y_train, _, _ = data
    return Screener().fit(X_train.copy(), y_train.copy())


def scores(screener, X):
    return np.asarray(screener.score(X.copy()), dtype=float).reshape(-1)


def fitted_model(screener):
    """The screener's fitted logistic regression: an attribute, or a pipeline's last step."""
    for value in vars(screener).values():
        if hasattr(value, "steps"):
            value = value.steps[-1][1]
        if hasattr(value, "coef_") and hasattr(value, "intercept_"):
            return value
    raise AttributeError("the screener keeps no fitted LogisticRegression")


@pytest.mark.id("tst_0gj3ni")
def test_direction(data, screener, yours):
    """Higher scores mean more likely malignant"""
    assert np.corrcoef(scores(screener, data[2]), yours)[0, 1] > 0.9


@pytest.mark.id("tst_012aru")
def test_alone_as_in_a_batch(data, screener):
    """Scores a sample the same alone as in a batch"""
    X_test = data[2]
    batch = scores(screener, X_test)
    alone = np.array([scores(screener, X_test[i : i + 1])[0] for i in range(5)])
    assert np.max(np.abs(alone - batch[:5])) <= 1e-9


@pytest.mark.id("tst_8shgp2")
def test_leaves_the_array(data, screener):
    """Leaves the clinic's array as it was"""
    given = data[2].copy()
    screener.score(given)
    assert np.array_equal(given, data[2])


@pytest.mark.id("tst_0xc7i0")
def test_missing_measurement(data, screener):
    """Never passes over a missing measurement"""
    X = data[2][:5].copy()
    X[2, 7] = np.nan
    try:
        p = np.asarray(screener.score(X), dtype=float).reshape(-1)
    except Exception:
        return
    assert p[2] >= 1.0, "a sample with a missing measurement was scored as usual"


@pytest.mark.id("tst_fustar")
def test_your_model(data, scaled, yours):
    """Gives the scores of the model you built"""
    X_train, y_train, _, _ = data
    model = fitted_model(Screener().fit(X_train.copy(), y_train.copy()))
    z = scaled[1] @ np.asarray(model.coef_, dtype=float).reshape(-1)
    p = np.exp(
        -np.logaddexp(0.0, -(z + float(np.asarray(model.intercept_).reshape(-1)[0])))
    )
    assert np.max(np.abs(p - yours)) <= 0.02
