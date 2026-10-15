import numpy as np
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from cv import features, fold_errors, folds


@pytest.fixture(scope="module")
def records():
    """The plant's records, the lab's training and validation tests: (X, y, mixes)."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    return table[kept, 3:], table[kept, 2], table[kept, 1]


def dealt(mixes, k, seed):
    """Each test's fold: the mixes shuffled, then dealt to the folds in turn."""
    order = np.random.default_rng(seed).permutation(np.unique(mixes))
    fold_of = {mix: number % k for number, mix in enumerate(order)}
    return np.array([fold_of[mix] for mix in mixes])


def as_rows(splits):
    return [
        (np.asarray(fit, dtype=int), np.asarray(held, dtype=int))
        for fit, held in splits
    ]


@pytest.mark.id("tst_lefwcj")
def test_each_test_held_out_once(records):
    """Every test is held out by exactly one fold"""
    mixes = records[2]
    held = np.concatenate([held for _, held in as_rows(folds(mixes.copy(), 5, 0))])
    assert sorted(held.tolist()) == list(range(len(mixes)))


@pytest.mark.id("tst_r2g163")
def test_fit_and_held_out_make_every_test(records):
    """Each fold fits on every test it doesn't hold out"""
    mixes = records[2]
    for fit, held in as_rows(folds(mixes.copy(), 5, 0)):
        assert np.intersect1d(fit, held).size == 0
        assert sorted(np.concatenate([fit, held]).tolist()) == list(range(len(mixes)))


@pytest.mark.id("tst_ro53wp")
def test_no_fold_splits_a_mix(records):
    """No fold splits a mix"""
    mixes = records[2]
    for fit, held in as_rows(folds(mixes.copy(), 5, 0)):
        assert np.intersect1d(mixes[fit], mixes[held]).size == 0


@pytest.mark.id("tst_vokzve")
def test_mixes_dealt_in_turn(records):
    """The shuffled mixes are dealt to the folds in turn"""
    mixes = records[2]
    for k, seed in ((5, 0), (3, 7), (10, 1)):
        splits = as_rows(folds(mixes.copy(), k, seed))
        fold = dealt(mixes, k, seed)
        assert len(splits) == k
        for i, (fit, held) in enumerate(splits):
            assert held.tolist() == np.flatnonzero(fold == i).tolist()
            assert fit.tolist() == np.flatnonzero(fold != i).tolist()


@pytest.mark.id("tst_sl9mey")
def test_one_row_per_fold(records):
    """One row per fold, one column per penalty"""
    X, y, mixes = records
    errors = np.asarray(
        fold_errors(features(X, 1), y, folds(mixes, 4, 0), [0.1, 1, 10])
    )
    assert errors.shape == (4, 3)


@pytest.mark.id("tst_8h3axk")
def test_same_errors_as_scikit_learn(records):
    """The same errors as scikit-learn, standardized and fit on each fold's fit tests"""
    X, y, mixes = records
    splits = as_rows(folds(mixes.copy(), 5, 0))
    penalties = [0.001, 0.1]
    errors = np.asarray(
        fold_errors(features(X, 2), y.copy(), splits, penalties), dtype=float
    )
    for i, (fit, held) in enumerate(splits):
        for j, penalty in enumerate(penalties):
            exact = make_pipeline(
                PolynomialFeatures(2, include_bias=False),
                StandardScaler(),
                Ridge(alpha=penalty * len(fit)),
            ).fit(X[fit], y[fit])
            expected = np.sqrt(np.mean((y[held] - exact.predict(X[held])) ** 2))
            assert errors[i, j] == pytest.approx(expected, abs=1e-6)
