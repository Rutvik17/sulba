from itertools import combinations_with_replacement

import numpy as np

# The worked example's model: the pair 5-fold cross-validation chooses in stage 2.
DEGREE, PENALTY = 3, 0.001


def features(X, degree):
    return np.column_stack(
        [
            np.prod(X[:, list(columns)], axis=1)
            for size in range(1, degree + 1)
            for columns in combinations_with_replacement(range(X.shape[1]), size)
        ]
    )


def folds(mixes, k, seed):
    order = np.random.default_rng(seed).permutation(np.unique(mixes))
    fold_of = {mix: number % k for number, mix in enumerate(order)}
    fold = np.array([fold_of[mix] for mix in mixes])
    return [(np.flatnonzero(fold != i), np.flatnonzero(fold == i)) for i in range(k)]


def error(P, y, fit, held, penalty):
    mean, std = P[fit].mean(axis=0), P[fit].std(axis=0)
    Z_fit, Z_held = (P[fit] - mean) / std, (P[held] - mean) / std
    centered = Z_fit - Z_fit.mean(axis=0)
    w = np.linalg.solve(
        centered.T @ centered + len(fit) * penalty * np.eye(P.shape[1]),
        centered.T @ (y[fit] - y[fit].mean()),
    )
    b = y[fit].mean() - Z_fit.mean(axis=0) @ w
    return float(np.sqrt(np.mean((y[held] - (Z_held @ w + b)) ** 2)))


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    X, y, mixes = table[kept, 3:], table[kept, 2], table[kept, 1]
    found = {
        "tests": f"{kept.sum():,}",
        "mixes": str(len(np.unique(mixes))),
        "test_tests": str(int((~kept).sum())),
        "test_mixes": str(len(np.unique(table[~kept, 1]))),
        "penalty": str(PENALTY),
    }
    P = features(X, DEGREE)
    errors = []
    for i, (fit, held) in enumerate(folds(mixes, 5, 0), start=1):
        errors.append(error(P, y, fit, held, PENALTY))
        found[f"mixes_{i}"] = str(len(np.unique(mixes[held])))
        found[f"tests_{i}"] = str(len(held))
        found[f"rmse_{i}"] = f"{errors[-1]:.2f}"
    found["mean"] = f"{np.mean(errors):.2f}"
    return found
