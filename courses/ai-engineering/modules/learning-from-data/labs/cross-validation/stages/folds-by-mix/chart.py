import numpy as np

from cv import features, fold_errors, folds

DEGREE, PENALTY = 3, 0.001
TOP = 12
# An error above the chart is drawn at its top, the same in every runtime.
OFF_CHART = 12.0


def chart(k):
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    X, y, mixes = table[kept, 3:], table[kept, 2], table[kept, 1]
    k = int(k)
    splits = folds(mixes, k, 0)
    errors = np.asarray(
        fold_errors(features(X, DEGREE), y, splits, [PENALTY]), dtype=float
    )
    errors = errors[:, 0]
    mean = float(errors.mean())

    def shown(value):
        return round(float(value), 2) if value <= TOP else OFF_CHART

    return {
        "x": {"min": 1, "max": k, "step": 1, "label": "fold"},
        "y": {"min": 0, "max": TOP, "step": 3, "label": "RMSE, MPa"},
        "lines": [
            {
                "style": "dashed",
                "label": "Mean of the folds",
                "x": [1, k],
                "y": [shown(mean), shown(mean)],
            },
        ],
        "points": [
            {"x": number, "y": shown(error)}
            for number, error in enumerate(errors, start=1)
        ],
        "readouts": [
            {"label": "Mean of the folds", "value": f"{mean:.2f} MPa"},
            {
                "label": "Lowest and highest fold",
                "value": f"{errors.min():.2f} to {errors.max():.2f} MPa",
            },
        ],
        "description": (
            f"Your RMSE in each of {k} folds by mix, at degree {DEGREE} with a penalty of "
            f"{PENALTY:g}: from {errors.min():.2f} to {errors.max():.2f} MPa, with a mean "
            f"of {mean:.2f} MPa."
        ),
    }
