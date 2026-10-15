import math
from itertools import combinations_with_replacement

import numpy as np
from sklearn.model_selection import train_test_split


def features(X, degree):
    return np.column_stack(
        [
            np.prod(X[:, list(columns)], axis=1)
            for size in range(1, degree + 1)
            for columns in combinations_with_replacement(range(X.shape[1]), size)
        ]
    )


def errors(X_train, y_train, X_val, y_val, degree):
    """Least squares on standardized features of `degree`: (train_rmse, val_rmse)."""
    P_train, P_val = features(X_train, degree), features(X_val, degree)
    mean, std = P_train.mean(axis=0), P_train.std(axis=0)
    P_train, P_val = (P_train - mean) / std, (P_val - mean) / std
    A = np.column_stack([P_train, np.ones(len(P_train))])
    theta, *_ = np.linalg.lstsq(A, y_train, rcond=None)
    w, b = theta[:-1], theta[-1]

    def rmse(y, P):
        return float(np.sqrt(np.mean((y - (P @ w + b)) ** 2)))

    return rmse(y_train, P_train), rmse(y_val, P_val)


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, mix, y, X = table[:, 0], table[:, 1], table[:, 2], table[:, 3:]
    train, val = part == 0, part == 1
    found = {}
    for number, name in enumerate(["train", "val", "test"]):
        found[f"{name}_tests"] = str(int((part == number).sum()))
        found[f"{name}_mixes"] = str(len(np.unique(mix[part == number])))
    for degree in range(1, 5):
        train_rmse, val_rmse = errors(X[train], y[train], X[val], y[val], degree)
        found[f"count_{degree}"] = str(math.comb(X.shape[1] + degree, degree) - 1)
        found[f"train_{degree}"] = f"{train_rmse:.2f}"
        # Degree 4 has more features than its training tests can pin down, so its validation
        # error is shown only by its size, the same in every runtime.
        found[f"val_{degree}"] = f"{val_rmse:.2f}" if val_rmse < 1000 else "over 1,000"
    # The training and validation tests split at random instead, as many held out as the
    # validation set has.
    seen = np.flatnonzero(train | val)
    fitted, held = train_test_split(seen, test_size=int(val.sum()), random_state=0)
    found["held"] = str(len(held))
    found["twins"] = str(int(np.isin(mix[held], mix[fitted]).sum()))
    return found
