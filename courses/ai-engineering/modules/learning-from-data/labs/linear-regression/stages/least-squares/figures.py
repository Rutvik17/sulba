import numpy as np


def about(value):
    """A large number to two significant figures, as the prose shows it."""
    return f"{float(f'{value:.2g}'):,.0f}"


def figures():
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, y_train, X_test, y_test = X[~test], y[~test], X[test], y[test]
    A = np.column_stack([X_train, np.ones(len(X_train))])
    theta, *_ = np.linalg.lstsq(A, y_train, rcond=None)
    w, b = theta[:-1], theta[-1]
    rmse = np.sqrt(np.mean((y_test - (X_test @ w + b)) ** 2))
    return {
        "cond_a": about(np.linalg.cond(A)),
        "cond_ata": about(np.linalg.cond(A.T @ A)),
        "w_temperature": f"{w[0]:.3f}",
        "w_vacuum": f"{w[1]:.3f}",
        "w_pressure": f"{w[2]:.3f}",
        "w_humidity": f"{w[3]:.3f}",
        "w_temperature_size": f"{abs(w[0]):.2f}",
        "bias": f"{b:.1f}",
        "rmse": f"{rmse:.2f}",
        "rmse_mean": f"{np.sqrt(np.mean((y_test - y_train.mean()) ** 2)):.1f}",
    }
