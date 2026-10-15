import numpy as np

from model import features, ridge, rmse, standardize

DEGREE = 3
TOP = 100


def chart(penalty):
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, y, X = table[:, 0], table[:, 2], table[:, 3:]
    train, val = part == 0, part == 1
    P_train, P_val = standardize(features(X[train], DEGREE), features(X[val], DEGREE))
    w, b = ridge(P_train, y[train], penalty)
    predicted = P_val @ w + b
    return {
        "x": {"min": 0, "max": TOP, "step": 10, "label": "measured strength, MPa"},
        "y": {"min": 0, "max": TOP, "step": 10, "label": "predicted strength, MPa"},
        "lines": [
            {
                "style": "dashed",
                "label": "Predicted as measured",
                "x": [0, TOP],
                "y": [0, TOP],
            },
        ],
        "points": [
            {"x": float(measured), "y": round(float(guess), 2)}
            for measured, guess in zip(y[val], predicted, strict=True)
        ],
        "readouts": [
            {
                "label": "Training RMSE",
                "value": f"{rmse(y[train], P_train @ w + b):.2f} MPa",
            },
            {"label": "Validation RMSE", "value": f"{rmse(y[val], predicted):.2f} MPa"},
        ],
        "description": (
            f"Your predicted strength against the measured strength of the "
            f"{int(val.sum())} validation tests, at degree {DEGREE} with a penalty of "
            f"{penalty:g}. The validation RMSE is {rmse(y[val], predicted):.2f} MPa."
        ),
    }
