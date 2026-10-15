import numpy as np

RATES = {
    "0_01": 0.01,
    "0_03": 0.03,
    "0_1": 0.1,
    "0_2": 0.2,
    "0_3": 0.3,
    "0_4": 0.4,
    "0_42": 0.42,
}
MAX_STEPS = 5_000


def descend(X, y, X_test, exact, lr):
    """Gradient descent at one rate: the steps it takes to come within 0.01 MW of least
    squares on every test hour, or None, and whether the loss fell at each step."""
    w, b = np.zeros(X.shape[1]), float(np.mean(y))
    previous, falls = np.inf, True
    for step in range(1, MAX_STEPS + 1):
        error = X @ w + b - y
        w = w - lr * 2 * X.T @ error / len(y)
        b = b - lr * 2 * float(np.mean(error))
        loss = float(np.mean((X @ w + b - y) ** 2))
        if not np.isfinite(loss):
            return None, False
        falls = falls and loss <= previous + 1e-12
        previous = loss
        if np.max(np.abs(X_test @ w + b - exact)) <= 0.01:
            return step, falls
    return None, falls


def figures():
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, y_train, X_test = X[~test], y[~test], X[test]
    mean, std = X_train.mean(axis=0), X_train.std(axis=0)
    Z, Z_test = (X_train - mean) / std, (X_test - mean) / std
    ones = np.ones((len(Z), 1))
    A = np.hstack([Z, ones])
    theta, *_ = np.linalg.lstsq(A, y_train, rcond=None)
    exact = Z_test @ theta[:-1] + theta[-1]
    # The mean squared error's curvature: the eigenvalues of its second derivatives.
    curvature = np.linalg.eigvalsh(2 * A.T @ A / len(Z))

    found = {
        "pressure_mean": f"{mean[2]:,.0f}",
        "pressure_std": f"{std[2]:.1f}",
        "cond_raw": f"{float(f'{np.linalg.cond(np.hstack([X_train, ones])):.2g}'):,.0f}",
        "cond_scaled": f"{np.linalg.cond(A):.1f}",
        "lambda_max": f"{curvature[-1]:.3f}",
        "lr_max": f"{2 / curvature[-1]:.3f}",
    }
    for name, lr in RATES.items():
        steps, falls = descend(Z, y_train, Z_test, exact, lr)
        found[f"steps_{name}"] = f"{steps:,}" if steps else f"Not within {MAX_STEPS:,}"
        found[f"falls_{name}"] = "Yes" if falls else "No"
    return found
