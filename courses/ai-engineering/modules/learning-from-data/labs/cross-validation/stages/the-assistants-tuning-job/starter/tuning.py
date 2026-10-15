"""The plant's tuning job: chooses the strength model's degree and penalty by five-fold
cross-validation over the plant's records, fits it on every record, and says how far off it
will be on mixes the plant hasn't made yet."""

import numpy as np

from cv import features, ridge

DEGREES = [1, 2, 3]
PENALTIES = [0.0001, 0.001, 0.01]
K = 5


def records(table):
    """The plant's records, from its table of tests: (X, y, mixes)."""
    return table[:, 3:], table[:, 2], table[:, 1]


def splits(mixes, seed=0):
    """Five folds of the plant's records, each holding out a fifth of them."""
    order = np.random.default_rng(seed).permutation(len(mixes))
    fold = np.empty(len(mixes), dtype=int)
    fold[order] = np.arange(len(mixes)) % K
    return [(np.flatnonzero(fold != i), np.flatnonzero(fold == i)) for i in range(K)]


def fitted(P, y, penalty):
    """Ridge regression on P standardized with its own columns: a function from features
    to strengths."""
    mean, std = P.mean(axis=0), P.std(axis=0)
    ((w, b),) = ridge((P - mean) / std, y, [penalty])
    return lambda Q: ((Q - mean) / std) @ w + b


def scores(X, y, mixes, seed=0):
    """Each degree and penalty's mean RMSE over the five folds."""
    found = {}
    for degree in DEGREES:
        P = features(X, degree)
        errors = np.zeros(len(PENALTIES))
        # Standardized once for every fold, so no fold has to do it again.
        Z = (P - P.mean(axis=0)) / P.std(axis=0)
        for fit, held in splits(mixes, seed):
            for j, (w, b) in enumerate(ridge(Z[fit], y[fit], PENALTIES)):
                errors[j] += np.sqrt(np.mean((y[held] - (Z[held] @ w + b)) ** 2)) / K
        for j, penalty in enumerate(PENALTIES):
            found[degree, penalty] = float(errors[j])
    return found


def choose(found):
    """The degree and penalty with the lowest RMSE."""
    return min(found, key=found.get)


def expected_error(X, y, mixes):
    """The RMSE to expect on mixes the plant hasn't made yet."""
    found = scores(X, y, mixes)
    return found[choose(found)]


def tuned(X, y, mixes):
    """The chosen model, fit on the plant's records: a function from mixes to strengths."""
    degree, penalty = choose(scores(X, y, mixes))
    model = fitted(features(X, degree), y, penalty)
    return lambda new: model(features(new, degree))
