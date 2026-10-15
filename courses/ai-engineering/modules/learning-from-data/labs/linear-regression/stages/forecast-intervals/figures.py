import math

import numpy as np
from sklearn.linear_model import LinearRegression

COVERAGE = 0.9


def figures():
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, y_train, X_test, y_test = X[~test], y[~test], X[test], y[test]
    held = np.arange(len(y_train)) % 5 == 0
    model = LinearRegression().fit(X_train[~held], y_train[~held])
    sizes = np.sort(np.abs(y_train[held] - model.predict(X_train[held])))
    n = len(sizes)
    k = math.ceil((n + 1) * COVERAGE)
    q = float(sizes[k - 1])
    inside = np.abs(y_test - model.predict(X_test)) <= q
    # The share inside in each quarter of the test hours, coldest to hottest.
    quarters = np.array_split(np.argsort(X_test[:, 0], kind="stable"), 4)
    shares = [float(np.mean(inside[quarter])) for quarter in quarters]
    return {
        # Numbers in a formula go without thousands separators.
        "n_held": str(n),
        "k_exact": f"{(n + 1) * COVERAGE:.1f}",
        "k": str(k),
        "k_rank": f"{k:,}",
        "q": f"{q:.2f}",
        "width": f"{2 * q:.1f}",
        "inside": f"{np.mean(inside):.1%}",
        "n_test": f"{len(y_test):,}",
        "inside_lowest": f"{min(shares):.1%}",
        "inside_highest": f"{max(shares):.1%}",
    }
