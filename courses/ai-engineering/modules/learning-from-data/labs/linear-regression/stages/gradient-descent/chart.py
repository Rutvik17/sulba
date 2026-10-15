import numpy as np

from model import fit, mse, predict, standardize, train

STEPS = 200
SLOW = 0.03
# A loss this far above the chart breaks its line, so a run that blows up leaves the top.
OFF_CHART = 1e4


def shown(losses):
    losses = np.asarray(losses, dtype=float)
    return np.where(np.abs(losses) < OFF_CHART, losses, np.nan)


def chart(lr):
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, X_test = standardize(X[~test], X[test])
    y_train, y_test = y[~test], y[test]

    w, b, losses = train(X_train, y_train, lr=lr, steps=STEPS)
    _, _, slow = train(X_train, y_train, lr=SLOW, steps=STEPS)
    w_exact, b_exact = fit(X_train, y_train)
    minimum = mse(y_train, predict(X_train, w_exact, b_exact))
    last = float(np.asarray(losses, dtype=float)[-1])
    test_rmse = np.sqrt(mse(y_test, predict(X_test, w, b)))
    steps = np.arange(1, STEPS + 1)
    return {
        "x": {"min": 0, "max": STEPS, "step": 50, "label": "step"},
        "y": {"min": 0, "max": 100, "step": 20, "label": "mean squared error"},
        "lines": [
            {
                "style": "dashed",
                "label": "Least squares",
                "x": [0, STEPS],
                "y": [minimum, minimum],
            },
            {
                "style": "faint",
                "label": f"Learning rate {SLOW:g}",
                "x": steps,
                "y": shown(slow),
            },
            {
                "style": "main",
                "label": f"Learning rate {lr:g}",
                "x": steps,
                "y": shown(losses),
            },
        ],
        "points": [],
        "readouts": [
            {
                "label": f"Loss after {STEPS} steps",
                "value": f"{last:.4f}"
                if np.isfinite(last) and abs(last) < 1e9
                else "Too large",
            },
            {"label": "Least squares", "value": f"{minimum:.4f}"},
            {
                "label": "Test RMSE",
                "value": f"{test_rmse:.2f} MW"
                if np.isfinite(test_rmse)
                else "Not a number",
            },
        ],
        "description": (
            f"Your training loss over {STEPS} steps at learning rates {lr:g} and {SLOW:g}, "
            f"against least squares, {minimum:.4f}."
        ),
    }
