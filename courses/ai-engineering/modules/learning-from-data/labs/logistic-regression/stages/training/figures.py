import numpy as np
from sklearn.linear_model import LogisticRegression

RATES = {"0_5": 0.5, "1": 1, "2": 2, "4": 4, "8": 8, "16": 16, "32": 32}
MAX_STEPS = 10_000


def sigmoid(z):
    return np.exp(-np.logaddexp(0.0, -z))


def descend(X, y, X_test, exact, lr, l2):
    """Gradient descent at one rate: the steps it takes to come within 0.0001 of the
    exact model on every test sample, or None, and whether the loss fell at each step."""
    w, b = np.zeros(X.shape[1]), 0.0
    previous, falls = np.inf, True
    for step in range(1, MAX_STEPS + 1):
        error = sigmoid(X @ w + b) - y
        w = w - lr * (X.T @ error / len(y) + l2 * w)
        b = b - lr * float(np.mean(error))
        p = np.clip(sigmoid(X @ w + b), 1e-15, 1 - 1e-15)
        loss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)) + l2 / 2 * (w @ w)
        falls = falls and loss <= previous + 1e-12
        previous = loss
        if np.max(np.abs(sigmoid(X_test @ w + b) - exact)) <= 1e-4:
            return step, falls
    return None, falls


def figures():
    with open("data/breast-cancer.csv") as file:
        columns = file.readline().strip().split(",")[2:]
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, y_train, X_test, y_test = X[~test], y[~test], X[test], y[test]
    mean, std = X_train.mean(axis=0), X_train.std(axis=0)
    X_train_scaled, X_test_scaled = (X_train - mean) / std, (X_test - mean) / std
    l2 = 1 / len(y_train)

    exact = LogisticRegression(C=1.0, tol=1e-12, max_iter=10_000).fit(
        X_train_scaled, y_train
    )
    p_exact = exact.predict_proba(X_test_scaled)[:, 1]
    default = LogisticRegression().fit(X_train_scaled, y_train)
    default_gap = np.max(np.abs(default.predict_proba(X_test_scaled)[:, 1] - p_exact))

    # The worked example: the first training sample's mean area, scaled.
    area = columns.index("mean_area")
    x, mu, sigma = X_train[0, area], round(mean[area], 1), round(std[area], 1)
    scaled = f"{(x - mu) / sigma:.2f}"
    if scaled != f"{X_train_scaled[0, area]:.2f}":
        raise ValueError("The rounded mean and deviation change the scaled value.")

    found = {
        "n_train": str(len(y_train)),
        "n_test": str(len(y_test)),
        "area_mean": f"{mean[area]:,.0f}",
        "smoothness_mean": f"{mean[columns.index('mean_smoothness')]:.3f}",
        "area_x": f"{x:g}",
        "area_mu": f"{mu:.1f}",
        "area_sigma": f"{sigma:.1f}",
        "area_scaled": scaled,
        "correct": str(int(np.sum((p_exact >= 0.5) == (y_test == 1)))),
        "default_gap": f"{default_gap:.4f}",
    }
    for name, lr in RATES.items():
        steps, falls = descend(X_train_scaled, y_train, X_test_scaled, p_exact, lr, l2)
        found[f"steps_{name}"] = f"{steps:,}" if steps else f"Not within {MAX_STEPS:,}"
        found[f"falls_{name}"] = "Yes" if falls else "No"
    return found
