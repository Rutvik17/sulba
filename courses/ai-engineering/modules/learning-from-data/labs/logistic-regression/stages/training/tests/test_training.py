import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from model import predict_proba, standardize, train


def accuracy(p, y):
    """The share of samples labelled correctly when p of 0.5 or more means 1."""
    return np.mean((p >= 0.5) == (y == 1))


@pytest.fixture(scope="module")
def data():
    """The lab's training and test sets, as (X_train, y_train, X_test, y_test)."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    return X[~test], y[~test], X[test], y[test]


@pytest.fixture(scope="module")
def models(data):
    """The test set's probabilities from your model, trained with the defaults, and
    from scikit-learn's LogisticRegression(tol=1e-12)."""
    X_train, y_train, X_test, _ = data
    X_train_scaled, X_test_scaled = standardize(X_train.copy(), X_test.copy())
    w, b, _ = train(X_train_scaled, y_train, l2=1 / len(y_train))
    scaler = StandardScaler().fit(X_train)
    exact = LogisticRegression(C=1.0, tol=1e-12, max_iter=10_000).fit(
        scaler.transform(X_train), y_train
    )
    return (
        predict_proba(X_test_scaled, w, b),
        exact.predict_proba(scaler.transform(X_test))[:, 1],
    )


@pytest.mark.id("tst_kjuen9")
def test_mean_zero(data):
    """Training columns have mean 0"""
    X_train, _, X_test, _ = data
    scaled, _ = standardize(X_train.copy(), X_test.copy())
    assert np.max(np.abs(scaled.mean(axis=0))) <= 1e-9


@pytest.mark.id("tst_t0e5n4")
def test_deviation_one(data):
    """Training columns have standard deviation 1"""
    X_train, _, X_test, _ = data
    scaled, _ = standardize(X_train.copy(), X_test.copy())
    assert np.max(np.abs(scaled.std(axis=0) - 1)) <= 1e-9


@pytest.mark.id("tst_p8xp4t")
def test_test_set_uses_training_numbers(data):
    """The test set uses the training set's means and standard deviations"""
    X_train, _, X_test, _ = data
    _, scaled = standardize(X_train.copy(), X_test.copy())
    expected = StandardScaler().fit(X_train).transform(X_test)
    assert np.max(np.abs(scaled - expected)) <= 1e-9


@pytest.mark.id("tst_oca8ft")
def test_each_step_lowers_the_loss(data):
    """Each step lowers the loss"""
    X_train, y_train, X_test, _ = data
    scaled, _ = standardize(X_train.copy(), X_test.copy())
    _, _, losses = train(scaled, y_train, steps=200, l2=1 / len(y_train))
    assert len(losses) == 200
    assert np.all(np.diff(losses) <= 1e-12), "a step raised the loss"


@pytest.mark.id("tst_oyrxfs")
def test_matches_scikit_learn(models):
    """Matches scikit-learn on every test sample"""
    yours, exact = models
    assert np.max(np.abs(yours - exact)) <= 1e-4


@pytest.mark.id("tst_qoi6x9")
def test_accuracy(data, models):
    """Labels the test set as accurately as scikit-learn"""
    y_test = data[3]
    yours, exact = models
    assert accuracy(yours, y_test) == accuracy(exact, y_test)
