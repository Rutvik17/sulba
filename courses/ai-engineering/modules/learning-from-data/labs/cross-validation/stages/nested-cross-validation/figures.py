from collections import Counter
from itertools import combinations_with_replacement

import numpy as np

DEGREES = [1, 2, 3]
PENALTIES = [0.00001, 0.0001, 0.001, 0.01, 0.1]
K, SEED = 5, 0


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


def fitted(P, y, penalty):
    """Ridge on P standardized with its own columns: a function from features to strengths."""
    mean, std = P.mean(axis=0), P.std(axis=0)
    Z = (P - mean) / std
    centered = Z - Z.mean(axis=0)
    w = np.linalg.solve(
        centered.T @ centered + len(y) * penalty * np.eye(P.shape[1]),
        centered.T @ (y - y.mean()),
    )
    b = y.mean() - Z.mean(axis=0) @ w
    return lambda Q: ((Q - mean) / std) @ w + b


def rmse(y, y_hat):
    return float(np.sqrt(np.mean((y - y_hat) ** 2)))


def choose(X, y, splits):
    scores = {}
    for degree in DEGREES:
        P = features(X, degree)
        for penalty in PENALTIES:
            scores[degree, penalty] = np.mean(
                [
                    rmse(y[held], fitted(P[fit], y[fit], penalty)(P[held]))
                    for fit, held in splits
                ]
            )
    best = min(scores, key=scores.get)
    return best, float(scores[best])


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    X, y, mixes = table[kept, 3:], table[kept, 2], table[kept, 1]
    X_test, y_test = table[~kept, 3:], table[~kept, 2]

    (degree, penalty), best = choose(X, y, folds(mixes, K, SEED))
    if (degree, penalty) != (3, 0.001):
        raise ValueError("The prose names degree 3 with 0.001 as the pair chosen.")
    final = fitted(features(X, degree), y, penalty)

    errors, pairs = [], []
    for fit, held in folds(mixes, K, SEED):
        (d, p), _ = choose(X[fit], y[fit], folds(mixes[fit], K, SEED))
        pairs.append((d, p))
        errors.append(
            rmse(y[held], fitted(features(X[fit], d), y[fit], p)(features(X[held], d)))
        )
    counts = Counter(pairs)
    others = sorted(pair for pair in counts if pair != (degree, penalty))
    if any(d != 3 for d, _ in others) or len(others) != 2:
        raise ValueError("The prose names two other penalties, both at degree 3.")

    pairs_tried = len(DEGREES) * len(PENALTIES)
    return {
        "pairs_tried": str(pairs_tried),
        "best": f"{best:.2f}",
        "nested": f"{np.mean(errors):.2f}",
        "test": f"{rmse(y_test, final(features(X_test, degree))):.2f}",
        "chosen_degree": str(degree),
        "chosen_penalty": str(penalty),
        "outer_top": str(counts[degree, penalty]),
        "other_1": str(others[0][1]),
        "other_2": str(others[1][1]),
        "cv_fits": str(pairs_tried * K),
        "nested_fits": str(K * (pairs_tried * K + 1)),
    }
