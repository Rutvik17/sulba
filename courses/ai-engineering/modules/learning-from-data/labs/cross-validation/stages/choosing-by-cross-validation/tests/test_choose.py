from itertools import combinations_with_replacement

import numpy as np
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from cv import choose, holdout

PENALTIES = [0.00001, 0.0001, 0.001, 0.01, 0.1]


@pytest.fixture(scope="module")
def records():
    """The plant's records, the lab's training and validation tests: (X, y, mixes)."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    return table[kept, 3:], table[kept, 2], table[kept, 1]


def dealt(mixes, k, seed):
    """Each fold's (fit, held) rows: the mixes shuffled, then dealt to the folds in turn."""
    order = np.random.default_rng(seed).permutation(np.unique(mixes))
    fold_of = {mix: number % k for number, mix in enumerate(order)}
    fold = np.array([fold_of[mix] for mix in mixes])
    return [(np.flatnonzero(fold != i), np.flatnonzero(fold == i)) for i in range(k)]


def reference_errors(X, y, splits, degree, penalties):
    """Each penalty's mean RMSE over the splits, by ridge in NumPy on each fold's own
    standardization."""
    P = np.column_stack(
        [
            np.prod(X[:, list(columns)], axis=1)
            for size in range(1, degree + 1)
            for columns in combinations_with_replacement(range(X.shape[1]), size)
        ]
    )
    errors = np.empty((len(splits), len(penalties)))
    for i, (fit, held) in enumerate(splits):
        mean, std = P[fit].mean(axis=0), P[fit].std(axis=0)
        Z, Z_held = (P[fit] - mean) / std, (P[held] - mean) / std
        centered = Z - Z.mean(axis=0)
        gram, right = centered.T @ centered, centered.T @ (y[fit] - y[fit].mean())
        for j, penalty in enumerate(penalties):
            w = np.linalg.solve(gram + len(fit) * penalty * np.eye(len(gram)), right)
            b = y[fit].mean() - Z.mean(axis=0) @ w
            errors[i, j] = np.sqrt(np.mean((y[held] - (Z_held @ w + b)) ** 2))
    return errors.mean(axis=0)


@pytest.mark.id("tst_jflzod")
def test_holdout_is_first_fold(records):
    """One split holds out the first of five folds by mix"""
    mixes = records[2]
    for seed in (0, 3):
        splits = holdout(mixes.copy(), seed)
        assert len(splits) == 1
        fit, held = (np.asarray(rows, dtype=int) for rows in splits[0])
        expected_fit, expected_held = dealt(mixes, 5, seed)[0]
        assert held.tolist() == expected_held.tolist()
        assert fit.tolist() == expected_fit.tolist()


@pytest.mark.id("tst_1e65m5")
def test_holdout_seed_changes_split(records):
    """Another seed holds out other mixes"""
    mixes = records[2]
    first = np.asarray(holdout(mixes.copy(), 0)[0][1], dtype=int)
    second = np.asarray(holdout(mixes.copy(), 1)[0][1], dtype=int)
    assert set(mixes[first]) != set(mixes[second])


@pytest.mark.id("tst_d39r9n")
def test_chooses_lowest_mean_error(records):
    """Chooses the pair with the lowest mean error, as scikit-learn measures it"""
    X, y, mixes = records
    splits = dealt(mixes, 3, 0)
    found = {}
    for degree in (1, 2):
        for penalty in (0.001, 0.1):
            errors = []
            for fit, held in splits:
                exact = make_pipeline(
                    PolynomialFeatures(degree, include_bias=False),
                    StandardScaler(),
                    Ridge(alpha=penalty * len(fit)),
                ).fit(X[fit], y[fit])
                errors.append(np.sqrt(np.mean((y[held] - exact.predict(X[held])) ** 2)))
            found[degree, penalty] = np.mean(errors)
    degree, penalty, rmse = choose(X.copy(), y.copy(), splits, [1, 2], [0.001, 0.1])
    best = min(found, key=found.get)
    assert (degree, penalty) == best
    assert rmse == pytest.approx(found[best], abs=1e-6)


@pytest.mark.id("tst_lvxy2j")
def test_five_folds_choose(records):
    """On five folds with seed 0, chooses degree 3 with a penalty of 0.001"""
    X, y, mixes = records
    splits = dealt(mixes, 5, 0)
    degree, penalty, rmse = choose(X.copy(), y.copy(), splits, [1, 2, 3], PENALTIES)
    assert (degree, penalty) == (3, 0.001)
    assert rmse == pytest.approx(
        reference_errors(X, y, splits, 3, [0.001])[0], abs=1e-6
    )
