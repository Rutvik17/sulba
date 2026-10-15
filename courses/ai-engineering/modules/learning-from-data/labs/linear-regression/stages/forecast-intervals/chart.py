import numpy as np

from forecaster import COLUMNS, Forecaster, halfwidth, intervals

LEVELS = np.round(np.arange(0.5, 0.991, 0.01), 2)


def weather(X):
    return {name: X[:, column] for column, name in enumerate(COLUMNS)}


def chart(coverage):
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, y_train, X_test, y_test = X[~test], y[~test], X[test], y[test]
    held = np.arange(len(y_train)) % 5 == 0
    forecaster = Forecaster().fit(X_train[~held], y_train[~held])
    misses = y_train[held] - np.asarray(forecaster.forecast(weather(X_train[held])))

    def inside(level):
        q = halfwidth(misses.copy(), level)
        low, high = intervals(forecaster, weather(X_test), q)
        return q, float(
            np.mean((y_test >= np.asarray(low)) & (y_test <= np.asarray(high)))
        )

    shares = np.array([inside(level)[1] for level in LEVELS])
    q, share = inside(coverage)
    return {
        "x": {"min": 50, "max": 100, "step": 10, "label": "coverage asked for (%)"},
        "y": {"min": 50, "max": 100, "step": 10, "label": "test hours inside (%)"},
        "lines": [
            {
                "style": "dashed",
                "label": "Coverage asked for",
                "x": [50, 100],
                "y": [50, 100],
            },
            {
                "style": "main",
                "label": "Test hours inside",
                "x": LEVELS * 100,
                "y": shares * 100,
            },
        ],
        "points": [{"x": coverage * 100, "y": share * 100}],
        "readouts": [
            {"label": "Interval width", "value": f"{2 * q:.1f} MW"},
            {"label": "Test hours inside", "value": f"{share:.1%}"},
        ],
        "description": (
            f"For each coverage asked for from 50% to 99%, the share of test hours inside your "
            f"intervals. At {coverage:.0%}, the intervals are {2 * q:.1f} MW wide and hold "
            f"{share:.1%} of the test hours."
        ),
    }
