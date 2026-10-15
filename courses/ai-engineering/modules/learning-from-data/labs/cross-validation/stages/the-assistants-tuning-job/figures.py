from itertools import combinations_with_replacement

import numpy as np

DEGREES = [1, 2, 3]
PENALTIES = [0.0001, 0.001, 0.01]
K = 5


def features(X, degree):
    return np.column_stack(
        [
            np.prod(X[:, list(columns)], axis=1)
            for size in range(1, degree + 1)
            for columns in combinations_with_replacement(range(X.shape[1]), size)
        ]
    )


def by_mix(mixes):
    order = np.random.default_rng(0).permutation(np.unique(mixes))
    fold_of = {mix: number % K for number, mix in enumerate(order)}
    fold = np.array([fold_of[mix] for mix in mixes])
    return [(np.flatnonzero(fold != i), np.flatnonzero(fold == i)) for i in range(K)]


def by_test(mixes):
    """The assistant's folds: the tests dealt in turn, whatever their mix."""
    order = np.random.default_rng(0).permutation(len(mixes))
    fold = np.empty(len(mixes), dtype=int)
    fold[order] = np.arange(len(mixes)) % K
    return [(np.flatnonzero(fold != i), np.flatnonzero(fold == i)) for i in range(K)]


def ridge(Z, y, penalty):
    centered = Z - Z.mean(axis=0)
    w = np.linalg.solve(
        centered.T @ centered + len(y) * penalty * np.eye(Z.shape[1]),
        centered.T @ (y - y.mean()),
    )
    return w, y.mean() - Z.mean(axis=0) @ w


def fitted(P, y, penalty, scale=None):
    """Ridge on P standardized with `scale`, or with P's own columns."""
    mean, std = scale if scale else (P.mean(axis=0), P.std(axis=0))
    w, b = ridge((P - mean) / std, y, penalty)
    return lambda Q: ((Q - mean) / std) @ w + b


def rmse(y, y_hat):
    return float(np.sqrt(np.mean((y - y_hat) ** 2)))


def scores(X, y, mixes, splits=by_mix, once=False):
    found = {}
    for degree in DEGREES:
        P = features(X, degree)
        scale = (P.mean(axis=0), P.std(axis=0)) if once else None
        for penalty in PENALTIES:
            found[degree, penalty] = np.mean(
                [
                    rmse(y[held], fitted(P[fit], y[fit], penalty, scale)(P[held]))
                    for fit, held in splits(mixes)
                ]
            )
    return found


def nested(X, y, mixes, splits=by_mix, once=False):
    errors = []
    for fit, held in splits(mixes):
        found = scores(X[fit], y[fit], mixes[fit], splits, once)
        degree, penalty = min(found, key=found.get)
        model = fitted(features(X[fit], degree), y[fit], penalty)
        errors.append(rmse(y[held], model(features(X[held], degree))))
    return float(np.mean(errors))


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    X, y, mixes = table[kept, 3:], table[kept, 2], table[kept, 1]
    X_new, y_new = table[~kept, 3:], table[~kept, 2]

    found = scores(X, y, mixes)
    degree, penalty = min(found, key=found.get)
    final = fitted(features(X, degree), y, penalty)

    # Tuned and fit on every test, the test set included, then checked on the test set.
    X_all, y_all, mixes_all = table[:, 3:], table[:, 2], table[:, 1]
    found_all = scores(X_all, y_all, mixes_all)
    d_all, p_all = min(found_all, key=found_all.get)
    leaked = fitted(features(X_all, d_all), y_all, p_all)

    # By test: how many held-out tests had their mix among their fold's fit tests.
    shared = sum(np.isin(mixes[held], mixes[fit]).sum() for fit, held in by_test(mixes))
    leaky = scores(X, y, mixes, by_test)
    # Standardized once: how far every score moved.
    once = scores(X, y, mixes, once=True)
    moved = max(abs(once[pair] - found[pair]) for pair in found)

    # What the assistant's job would have told the plant, with all four problems.
    told = min(scores(X_all, y_all, mixes_all, by_test, once=True).values())

    return {
        "chosen_score": f"{found[degree, penalty]:.2f}",
        "all_tests": f"{len(y_all):,}",
        "test_tests": str(int((~kept).sum())),
        "leaked_new": f"{rmse(y_new, leaked(features(X_new, d_all))):.2f}",
        "final_new": f"{rmse(y_new, final(features(X_new, degree))):.2f}",
        "records": str(len(y)),
        "pairs": str(len(DEGREES) * len(PENALTIES)),
        "shared": str(int(shared)),
        "leaky_score": f"{min(leaky.values()):.2f}",
        "moved": f"{moved:.2f}",
        "once_chosen": f"{once[degree, penalty]:.2f}",
        "nested": f"{nested(X, y, mixes):.2f}",
        "told": f"{told:.2f}",
    }
