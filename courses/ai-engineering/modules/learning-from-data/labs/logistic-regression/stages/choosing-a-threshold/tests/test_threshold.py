import numpy as np
import pytest

from screener import Screener, best_threshold, precision_recall


@pytest.fixture(scope="module")
def data():
    """The lab's training and test sets, as (X_train, y_train, X_test, y_test)."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    return X[~test], y[~test], X[test], y[test]


@pytest.fixture(scope="module")
def scored(data):
    """The test set's labels, and your screener's probabilities for it."""
    X_train, y_train, X_test, y_test = data
    screener = Screener().fit(X_train.copy(), y_train.copy())
    return y_test, np.asarray(screener.score(X_test.copy()), dtype=float).reshape(-1)


def _precision_recall(y, p, threshold=0.5):
    predicted = p >= threshold
    hits = np.sum(predicted & (y == 1))
    precision = hits / np.sum(predicted) if np.any(predicted) else 0.0
    return float(precision), float(hits / np.sum(y == 1))


def _best_threshold(y, p, min_recall):
    positives = np.sort(p[y == 1])[::-1]
    needed = max(1, int(np.ceil(min_recall * len(positives) - 1e-9)))
    return float(positives[needed - 1])


@pytest.mark.id("tst_79fqyy")
def test_precision(scored):
    """Precision at 0.5"""
    y, p = scored
    expected = _precision_recall(y, p)[0]
    assert precision_recall(y.copy(), p.copy())[0] == pytest.approx(expected)


@pytest.mark.id("tst_zsujo9")
def test_recall(scored):
    """Recall at 0.5"""
    y, p = scored
    expected = _precision_recall(y, p)[1]
    assert precision_recall(y.copy(), p.copy())[1] == pytest.approx(expected)


@pytest.mark.id("tst_jx6m67")
def test_lower_threshold(scored):
    """A lower threshold"""
    y, p = scored
    expected = _precision_recall(y, p, 0.2)
    assert tuple(precision_recall(y.copy(), p.copy(), 0.2)) == pytest.approx(expected)


@pytest.mark.id("tst_9bs0j9")
def test_nothing_predicted(scored):
    """Nothing predicted positive"""
    y, p = scored
    assert tuple(precision_recall(y.copy(), p.copy(), 1.01)) == pytest.approx((0, 0))


@pytest.mark.id("tst_fohf1o")
def test_high_recall(scored):
    """98% recall"""
    y, p = scored
    expected = _best_threshold(y, p, 0.98)
    assert best_threshold(y.copy(), p.copy(), 0.98) == pytest.approx(expected)


@pytest.mark.id("tst_ok8rjt")
def test_half_the_positives(scored):
    """Half the positives"""
    y, p = scored
    expected = _best_threshold(y, p, 0.5)
    assert best_threshold(y.copy(), p.copy(), 0.5) == pytest.approx(expected)
