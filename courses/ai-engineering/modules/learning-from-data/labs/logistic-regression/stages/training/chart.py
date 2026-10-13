import numpy as np

from model import predict_proba, standardize, train

STEPS = 300
SLOW = 0.05


def lowest(X, y, l2):
    """The lowest loss there is: J at its minimum, found with Newton's method. Like
    J, it puts no l2 term on the bias."""
    A = np.hstack([X, np.ones((len(y), 1))])
    penalty = np.r_[np.full(X.shape[1], l2), 0.0]
    theta = np.zeros(A.shape[1])
    for _ in range(100):
        p = np.exp(-np.logaddexp(0.0, -(A @ theta)))
        slope = A.T @ (p - y) / len(y) + penalty * theta
        curvature = (A.T * (p * (1 - p))) @ A / len(y) + np.diag(penalty)
        step = np.linalg.solve(curvature, slope)
        theta = theta - step
        if np.max(np.abs(step)) < 1e-12:
            break
    p = np.clip(np.exp(-np.logaddexp(0.0, -(A @ theta))), 1e-15, 1 - 1e-15)
    w = theta[:-1]
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)) + l2 / 2 * w @ w)


def chart(lr):
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, X_test = standardize(X[~test], X[test])
    y_train, y_test = y[~test], y[test]
    l2 = 1 / len(y_train)

    w, b, losses = train(X_train, y_train, lr=lr, steps=STEPS, l2=l2)
    _, _, slow = train(X_train, y_train, lr=SLOW, steps=STEPS, l2=l2)
    accuracy = np.mean((predict_proba(X_test, w, b) >= 0.5) == (y_test == 1))
    minimum = lowest(np.asarray(X_train, dtype=float), y_train, l2)
    last = float(losses[-1])
    steps = np.arange(1, STEPS + 1)
    return {
        "x": {"min": 0, "max": STEPS, "step": 50, "label": "step"},
        "y": {"min": 0, "max": 0.8, "step": 0.2, "label": "loss"},
        "lines": [
            {
                "style": "dashed",
                "label": "Minimum",
                "x": [0, STEPS],
                "y": [minimum, minimum],
            },
            {
                "style": "faint",
                "label": f"Learning rate {SLOW:g}",
                "x": steps,
                "y": slow,
            },
            {
                "style": "main",
                "label": f"Learning rate {lr:g}",
                "x": steps,
                "y": losses,
            },
        ],
        "points": [],
        "readouts": [
            {"label": f"Loss after {STEPS} steps", "value": f"{last:.4f}"},
            {"label": "Minimum", "value": f"{minimum:.4f}"},
            {"label": "Test accuracy", "value": f"{accuracy * 100:.1f}%"},
        ],
        "description": (
            f"Your training loss over {STEPS} steps at learning rates {lr:g} and {SLOW:g}. "
            f"After {STEPS} steps it is {last:.4f}. The minimum is {minimum:.4f}."
        ),
    }
