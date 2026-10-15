from collections import Counter
from itertools import combinations_with_replacement

import numpy as np

DEGREES = [1, 2, 3]
PENALTIES = [0.00001, 0.0001, 0.001, 0.01, 0.1]
SEEDS = range(20)


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


def mean_errors(P, y, splits):
    """Each penalty's mean RMSE over the splits."""
    errors = np.empty((len(splits), len(PENALTIES)))
    for i, (fit, held) in enumerate(splits):
        mean, std = P[fit].mean(axis=0), P[fit].std(axis=0)
        Z, Z_held = (P[fit] - mean) / std, (P[held] - mean) / std
        centered = Z - Z.mean(axis=0)
        gram, right = centered.T @ centered, centered.T @ (y[fit] - y[fit].mean())
        for j, penalty in enumerate(PENALTIES):
            w = np.linalg.solve(gram + len(fit) * penalty * np.eye(len(gram)), right)
            b = y[fit].mean() - Z.mean(axis=0) @ w
            errors[i, j] = np.sqrt(np.mean((y[held] - (Z_held @ w + b)) ** 2))
    return errors.mean(axis=0)


def chosen(Ps, y, splits):
    scores = {
        (degree, PENALTIES[j]): error
        for degree, P in Ps.items()
        for j, error in enumerate(mean_errors(P, y, splits))
    }
    return min(scores, key=scores.get)


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, mix, y, X = table[:, 0], table[:, 1], table[:, 2], table[:, 3:]
    kept = part < 2
    Ps = {degree: features(X[kept], degree) for degree in DEGREES}
    y_kept, mixes = y[kept], mix[kept]
    found = {"seeds": str(len(SEEDS))}

    # The last lab's choice, on its fixed training and validation sets.
    train, val = np.flatnonzero(part[kept] == 0), np.flatnonzero(part[kept] == 1)
    last = chosen(Ps, y_kept, [(train, val)])
    found["last_penalty"] = str(last[1])

    for name, penalty in (("small", last[1]), ("chosen", 0.001)):
        j = PENALTIES.index(penalty)
        one = [mean_errors(Ps[3], y_kept, folds(mixes, 5, s)[:1])[j] for s in SEEDS]
        five = [mean_errors(Ps[3], y_kept, folds(mixes, 5, s))[j] for s in SEEDS]
        found[f"{name}_penalty"] = str(penalty)
        found[f"one_low_{name}"] = f"{min(one):.2f}"
        found[f"one_high_{name}"] = f"{max(one):.2f}"
        found[f"five_low_{name}"] = f"{min(five):.2f}"
        found[f"five_high_{name}"] = f"{max(five):.2f}"

    for name, k in (("one", 1), ("five", 5)):
        choices = Counter(chosen(Ps, y_kept, folds(mixes, 5, s)[:k]) for s in SEEDS)
        top, count = choices.most_common(1)[0]
        if top != (3, 0.001):
            raise ValueError(
                "The prose names degree 3 with 0.001 as the most chosen pair."
            )
        found[f"{name}_top"] = str(count)
        found["top_degree"], found["top_penalty"] = str(top[0]), str(top[1])
        found[f"{name}_other"] = str(len(SEEDS) - count)
        found[f"{name}_pairs"] = str(len(choices))
    return found
