"""The plant's tuning job: chooses the strength model's degree and penalty by five-fold
cross-validation over the plant's records, fits it on every record, and says how far off it
will be on mixes the plant hasn't made yet."""

import numpy as np

from cv import features, ridge

DEGREES = [1, 2, 3]
PENALTIES = [0.0001, 0.001, 0.01]
K = 5


def records(table):
    """The plant's records, from its table of tests, without the test set: (X, y, mixes)."""
    kept = table[:, 0] < 2
    return table[kept, 3:], table[kept, 2], table[kept, 1]


def splits(mixes, seed=0):
    """Five folds of the plant's records, each holding out a fifth of its mixes."""
    order = np.random.default_rng(seed).permutation(np.unique(mixes))
    fold_of = {mix: number % K for number, mix in enumerate(order)}
    fold = np.array([fold_of[mix] for mix in mixes])
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
        for fit, held in splits(mixes, seed):
            mean, std = P[fit].mean(axis=0), P[fit].std(axis=0)
            Z_fit, Z_held = (P[fit] - mean) / std, (P[held] - mean) / std
            for j, (w, b) in enumerate(ridge(Z_fit, y[fit], PENALTIES)):
                errors[j] += np.sqrt(np.mean((y[held] - (Z_held @ w + b)) ** 2)) / K
        for j, penalty in enumerate(PENALTIES):
            found[degree, penalty] = float(errors[j])
    return found


def choose(found):
    """The degree and penalty with the lowest RMSE."""
    return min(found, key=found.get)


def expected_error(X, y, mixes):
    """The RMSE to expect on mixes the plant hasn't made yet."""
    errors = []
    for fit, held in splits(mixes):
        degree, penalty = choose(scores(X[fit], y[fit], mixes[fit]))
        model = fitted(features(X[fit], degree), y[fit], penalty)
        errors.append(
            np.sqrt(np.mean((y[held] - model(features(X[held], degree))) ** 2))
        )
    return float(np.mean(errors))


def tuned(X, y, mixes):
    """The chosen model, fit on the plant's records: a function from mixes to strengths."""
    degree, penalty = choose(scores(X, y, mixes))
    model = fitted(features(X, degree), y, penalty)
    return lambda new: model(features(new, degree))


class TunedModel:
    """The tuning job's model: the degree and penalty with the lowest five-fold RMSE,
    averaged over a shuffle of the folds for each seed, fit on every record."""

    def __init__(self, X, y, mixes, seeds=(0, 1)):
        """Scores every pair once for each seed, chooses by the average, and fits the
        chosen pair on every record."""
        each = [scores(X, y, mixes, seed) for seed in seeds]
        self.scores = {
            pair: float(np.mean([found[pair] for found in each])) for pair in each[0]
        }
        self.degree, self.penalty = choose(self.scores)
        self.model = fitted(features(X, self.degree), y, self.penalty)

    def predict(self, new):
        """The strength in MPa of each new mix."""
        new = np.atleast_2d(np.asarray(new, dtype=float))
        return self.model(features(new, self.degree))
