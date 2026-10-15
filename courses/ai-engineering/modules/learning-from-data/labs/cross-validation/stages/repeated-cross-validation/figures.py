from itertools import combinations_with_replacement

import numpy as np

DEGREES = [1, 2, 3]
PENALTIES = [0.0001, 0.001, 0.01]
K = 5
SEEDS = 30
CHOSEN = (3, 0.001)


def features(X, degree):
    return np.column_stack(
        [
            np.prod(X[:, list(columns)], axis=1)
            for size in range(1, degree + 1)
            for columns in combinations_with_replacement(range(X.shape[1]), size)
        ]
    )


def folds(mixes, seed):
    order = np.random.default_rng(seed).permutation(np.unique(mixes))
    fold_of = {mix: number % K for number, mix in enumerate(order)}
    fold = np.array([fold_of[mix] for mix in mixes])
    return [(np.flatnonzero(fold != i), np.flatnonzero(fold == i)) for i in range(K)]


def fit(P, y, penalties):
    """Ridge on P standardized with its own columns, for each penalty: functions to strengths."""
    mean, std = P.mean(axis=0), P.std(axis=0)
    Z = (P - mean) / std
    centered = Z - Z.mean(axis=0)
    gram, right = centered.T @ centered, centered.T @ (y - y.mean())
    models = []
    for penalty in penalties:
        w = np.linalg.solve(gram + len(y) * penalty * np.eye(len(gram)), right)
        b = y.mean() - Z.mean(axis=0) @ w
        models.append(lambda Q, w=w, b=b: ((Q - mean) / std) @ w + b)
    return models


def rmse(y, y_hat):
    return float(np.sqrt(np.mean((y - y_hat) ** 2)))


def scores(Ps, y, mixes, seed):
    found = {}
    for degree, P in Ps.items():
        errors = np.zeros(len(PENALTIES))
        for fit_rows, held in folds(mixes, seed):
            for j, model in enumerate(fit(P[fit_rows], y[fit_rows], PENALTIES)):
                errors[j] += rmse(y[held], model(P[held])) / K
        for j, penalty in enumerate(PENALTIES):
            found[degree, penalty] = errors[j]
    return found


def chosen(each):
    average = {pair: np.mean([found[pair] for found in each]) for pair in each[0]}
    return min(average, key=average.get)


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    X, y, mixes = table[kept, 3:], table[kept, 2], table[kept, 1]
    Ps = {degree: features(X, degree) for degree in DEGREES}
    each = [scores(Ps, y, mixes, seed) for seed in range(SEEDS)]
    found = {
        "seeds": str(SEEDS),
        "cv_fits": str(len(DEGREES) * len(PENALTIES) * K),
        "chosen_degree": str(CHOSEN[0]),
        "chosen_penalty": str(CHOSEN[1]),
    }
    for name, size in (("one", 1), ("two", 2), ("three", 3), ("five", 5)):
        sets = [each[start : start + size] for start in range(0, SEEDS, size)]
        found[f"{name}_sets"] = str(len(sets))
        found[f"{name}_chose"] = str(sum(chosen(group) == CHOSEN for group in sets))
    found["two_fits"] = str(2 * len(DEGREES) * len(PENALTIES) * K)

    degree, penalty = chosen(each[:2])
    if (degree, penalty) != CHOSEN:
        raise ValueError("The prose names degree 3 with 0.001 as the shipped pair.")
    model = fit(Ps[degree], y, [penalty])[0]
    test = table[:, 0] == 2
    found["test"] = (
        f"{rmse(table[test, 2], model(features(table[test, 3:], degree))):.2f}"
    )
    found["records"] = str(len(y))
    return found
