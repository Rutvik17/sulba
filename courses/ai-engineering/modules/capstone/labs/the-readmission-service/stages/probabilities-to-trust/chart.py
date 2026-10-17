import numpy as np

from features import stays
from model import brier, calibration, out_of_fold


def chart(bins):
    table = stays("data/encounters.csv")
    y = table["readmitted"].to_numpy()
    p = out_of_fold(table)
    predicted, observed = (
        np.asarray(part, dtype=float) for part in calibration(y, p, int(bins))
    )
    # Probabilities to six places, which every runtime gives the same.
    predicted, observed = np.round(predicted, 6), np.round(observed, 6)
    top = float(max(predicted.max(), observed.max()))
    edge = float(np.ceil(top * 20) / 20)
    expected = float(np.sum(p))
    return {
        "x": {
            "min": 0,
            "max": edge,
            "step": 0.05,
            "label": "mean probability in the group",
        },
        "y": {
            "min": 0,
            "max": edge,
            "step": 0.05,
            "label": "share readmitted in the group",
        },
        "lines": [
            {"style": "dashed", "label": "Calibrated", "x": [0, edge], "y": [0, edge]},
            {"style": "main", "label": "Your model", "x": predicted, "y": observed},
        ],
        "points": [{"x": x, "y": s} for x, s in zip(predicted, observed, strict=True)],
        "readouts": [
            {"label": "Readmissions expected", "value": f"{expected:.0f}"},
            {"label": "Readmissions", "value": str(int(y.sum()))},
            {"label": "Brier score", "value": f"{brier(y, p):.4f}"},
        ],
        "description": (
            f"Your model's out-of-fold probabilities for {len(y):,} stays in {int(bins)} "
            f"groups: they add up to {expected:.0f} readmissions, for {int(y.sum())}, with a "
            f"Brier score of {brier(y, p):.4f}."
        ),
    }
