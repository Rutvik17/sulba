import numpy as np

from cv import features, fold_errors, folds, holdout

DEGREE = 3
SEEDS = range(20)
TOP = 30
# An estimate above the chart is drawn at its top, the same in every runtime.
OFF_CHART = 30.0


def shown(values):
    return [round(float(value), 2) if value <= TOP else OFF_CHART for value in values]


def chart(penalty):
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    X, y, mixes = table[kept, 3:], table[kept, 2], table[kept, 1]
    P = features(X, DEGREE)

    def estimate(splits):
        return float(np.mean(np.asarray(fold_errors(P, y, splits, [penalty]))[:, 0]))

    one = sorted(estimate(holdout(mixes, seed)) for seed in SEEDS)
    five = sorted(estimate(folds(mixes, 5, seed)) for seed in SEEDS)
    ranks = list(range(1, len(SEEDS) + 1))
    return {
        "x": {
            "min": 0,
            "max": len(SEEDS),
            "step": 5,
            "label": "estimate, lowest first",
        },
        "y": {"min": 0, "max": TOP, "step": 5, "label": "RMSE, MPa"},
        "lines": [
            {"style": "faint", "label": "One split", "x": ranks, "y": shown(one)},
            {"style": "main", "label": "Five folds", "x": ranks, "y": shown(five)},
        ],
        "points": [],
        "readouts": [
            {"label": "One split", "value": f"{one[0]:.2f} to {one[-1]:.2f} MPa"},
            {"label": "Five folds", "value": f"{five[0]:.2f} to {five[-1]:.2f} MPa"},
        ],
        "description": (
            f"Your estimates of the RMSE at degree {DEGREE} with a penalty of {penalty:g}, "
            f"one for each of {len(SEEDS)} seeds, lowest first. One split ranges from "
            f"{one[0]:.2f} to {one[-1]:.2f} MPa, and five folds from {five[0]:.2f} to "
            f"{five[-1]:.2f} MPa."
        ),
    }
