from itertools import combinations_with_replacement

import numpy as np
import pytest

from cv import nested

DEGREES = [1, 2]
PENALTIES = [0.001, 0.1]


@pytest.fixture(scope="module")
def records():
    """The plant's records, the lab's training and validation tests: (X, y, mixes)."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    return table[kept, 3:], table[kept, 2], table[kept, 1]


def dealt(mixes, k, seed):
    order = np.random.default_rng(seed).permutation(np.unique(mixes))
    fold_of = {mix: number % k for number, mix in enumerate(order)}
    fold = np.array([fold_of[mix] for mix in mixes])
    return [(np.flatnonzero(fold != i), np.flatnonzero(fold == i)) for i in range(k)]


def features(X, degree):
    return np.column_stack(
        [
            np.prod(X[:, list(columns)], axis=1)
            for size in range(1, degree + 1)
            for columns in combinations_with_replacement(range(X.shape[1]), size)
        ]
    )


def errors(P, y, splits, penalties):
    found = np.empty((len(splits), len(penalties)))
    for i, (fit, held) in enumerate(splits):
        mean, std = P[fit].mean(axis=0), P[fit].std(axis=0)
        Z, Z_held = (P[fit] - mean) / std, (P[held] - mean) / std
        centered = Z - Z.mean(axis=0)
        gram, right = centered.T @ centered, centered.T @ (y[fit] - y[fit].mean())
        for j, penalty in enumerate(penalties):
            w = np.linalg.solve(gram + len(fit) * penalty * np.eye(len(gram)), right)
            b = y[fit].mean() - Z.mean(axis=0) @ w
            found[i, j] = np.sqrt(np.mean((y[held] - (Z_held @ w + b)) ** 2))
    return found


def reference(X, y, mixes, k, seed):
    """Nested cross-validation as the brief describes it: (rmse, pairs)."""
    found, pairs = [], []
    for fit, held in dealt(mixes, k, seed):
        inner = dealt(mixes[fit], k, seed)
        scores = {
            (degree, PENALTIES[j]): error
            for degree in DEGREES
            for j, error in enumerate(
                errors(features(X[fit], degree), y[fit], inner, PENALTIES).mean(axis=0)
            )
        }
        degree, penalty = min(scores, key=scores.get)
        pairs.append((degree, penalty))
        found.append(errors(features(X, degree), y, [(fit, held)], [penalty])[0, 0])
    return float(np.mean(found)), pairs


def run(records, y=None, k=3, seed=0):
    X, y_records, mixes = records
    y = y_records if y is None else y
    rmse, pairs = nested(X.copy(), y.copy(), mixes.copy(), DEGREES, PENALTIES, k, seed)
    return rmse, [(int(degree), float(penalty)) for degree, penalty in pairs]


@pytest.mark.id("tst_u5c2t7")
def test_one_pair_per_outer_fold(records):
    """One pair per outer fold, each from the degrees and penalties given"""
    _, pairs = run(records)
    assert len(pairs) == 3
    for degree, penalty in pairs:
        assert degree in DEGREES and penalty in PENALTIES


@pytest.mark.id("tst_9uh8ty")
def test_chooses_on_outer_fit_tests(records):
    """Each outer fold chooses on its own fit tests, with folds of their mixes"""
    _, pairs = run(records, k=3, seed=2)
    assert pairs == reference(*records, 3, 2)[1]


@pytest.mark.id("tst_utk27j")
def test_same_estimate(records):
    """The same estimate as nested cross-validation done by hand"""
    rmse, _ = run(records, k=3, seed=2)
    assert rmse == pytest.approx(reference(*records, 3, 2)[0], abs=1e-6)


@pytest.mark.id("tst_x9gcgt")
def test_held_out_tests_never_reach_the_choice(records):
    """An outer fold's choice doesn't change when its held-out strengths do"""
    X, y, mixes = records
    held = dealt(mixes, 3, 0)[0][1]
    changed = y.copy()
    changed[held] += 50
    before, after = run(records), run(records, y=changed)
    assert after[1][0] == before[1][0]
    assert after[0] != pytest.approx(before[0])
