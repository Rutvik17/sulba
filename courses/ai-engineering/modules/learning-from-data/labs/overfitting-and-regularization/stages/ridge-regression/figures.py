from itertools import combinations_with_replacement

import numpy as np

DEGREES = [1, 2, 3, 4]
PENALTIES = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1]
# The penalties the table shows, from none.
SHOWN = [0, *PENALTIES]


def features(X, degree):
    return np.column_stack(
        [
            np.prod(X[:, list(columns)], axis=1)
            for size in range(1, degree + 1)
            for columns in combinations_with_replacement(range(X.shape[1]), size)
        ]
    )


def scaled(X_train, X_val, degree):
    P_train, P_val = features(X_train, degree), features(X_val, degree)
    mean, std = P_train.mean(axis=0), P_train.std(axis=0)
    return (P_train - mean) / std, (P_val - mean) / std


def fit(P, y, penalty):
    """Ridge regression, or least squares when the penalty is 0, as (w, b)."""
    if penalty == 0:
        theta, *_ = np.linalg.lstsq(
            np.column_stack([P, np.ones(len(P))]), y, rcond=None
        )
        return theta[:-1], theta[-1]
    mean = P.mean(axis=0)
    centered = P - mean
    n, d = P.shape
    w = np.linalg.solve(
        centered.T @ centered + n * penalty * np.eye(d), centered.T @ (y - y.mean())
    )
    return w, y.mean() - mean @ w


def penalty_text(penalty):
    return np.format_float_positional(penalty, trim="-")


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, y, X = table[:, 0], table[:, 2], table[:, 3:]
    X_train, y_train = X[part == 0], y[part == 0]
    X_val, y_val = X[part == 1], y[part == 1]
    found = {"n": str(len(y_train))}
    best = None
    for degree in DEGREES:
        P_train, P_val = scaled(X_train, X_val, degree)
        for penalty in SHOWN:
            w, b = fit(P_train, y_train, penalty)
            score = float(np.sqrt(np.mean((y_val - (P_val @ w + b)) ** 2)))
            key = f"val_{degree}_{SHOWN.index(penalty)}"
            # Least squares at degree 4 can't be pinned down, so only its size is shown.
            found[key] = f"{score:.2f}" if score < 1000 else "over 1,000"
            if penalty > 0 and (best is None or score < best[2]):
                best = (degree, penalty, score)
    for index, penalty in enumerate(SHOWN):
        found[f"penalty_{index}"] = penalty_text(penalty)
    degree, penalty, score = best
    found["best_degree"] = str(degree)
    found["best_penalty"] = penalty_text(penalty)
    found["best_val"] = f"{score:.2f}"
    found["alpha"] = penalty_text(len(y_train) * penalty)
    found["cement_cubed"] = f"{X_train[:, 0].max() ** 3:,.0f}"
    return found
