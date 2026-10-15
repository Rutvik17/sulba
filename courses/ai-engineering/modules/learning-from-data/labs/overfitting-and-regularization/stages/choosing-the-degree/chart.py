import numpy as np

from model import errors

DEGREES = [1, 2, 3, 4]
TOP = 20
# An error above the chart is drawn at this height, so its line leaves the top the same way in
# every runtime, however far above it is.
OFF_CHART = 25.0


def shown(values):
    return [round(value, 2) if value <= TOP else OFF_CHART for value in values]


def chart(mixes):
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, mix, y, X = table[:, 0], table[:, 1], table[:, 2], table[:, 3:]
    train, val = part == 0, part == 1
    # The first `mixes` training mixes by number, with every test of each.
    kept = train & np.isin(mix, np.unique(mix[train])[:mixes])
    scores = [errors(X[kept], y[kept], X[val], y[val], degree) for degree in DEGREES]
    train_rmse = [train_error for train_error, _ in scores]
    val_rmse = [val_error for _, val_error in scores]
    best = int(np.argmin(val_rmse))
    return {
        "x": {"min": 1, "max": 4, "step": 1, "label": "degree"},
        "y": {"min": 0, "max": TOP, "step": 5, "label": "RMSE, MPa"},
        "lines": [
            {
                "style": "faint",
                "label": "Training mixes",
                "x": DEGREES,
                "y": shown(train_rmse),
            },
            {
                "style": "main",
                "label": "Validation mixes",
                "x": DEGREES,
                "y": shown(val_rmse),
            },
        ],
        "points": [{"x": DEGREES[best], "y": round(val_rmse[best], 2)}],
        "readouts": [
            {"label": "Training tests", "value": f"{int(kept.sum()):,}"},
            {
                "label": "Lowest validation RMSE",
                "value": f"{val_rmse[best]:.2f} MPa, at degree {DEGREES[best]}",
            },
        ],
        "description": (
            f"Your training and validation RMSE at degrees 1 to 4, fit on {mixes} training "
            f"mixes. The validation RMSE is lowest at degree {DEGREES[best]}, "
            f"{val_rmse[best]:.2f} MPa."
        ),
    }
