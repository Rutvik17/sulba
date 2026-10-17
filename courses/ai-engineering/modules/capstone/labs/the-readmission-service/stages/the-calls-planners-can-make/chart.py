import numpy as np

from features import stays
from model import calls, out_of_fold, threshold_for


def chart(share):
    table = stays("data/encounters.csv")
    y = table["readmitted"].to_numpy()
    p = out_of_fold(table)
    shares = np.linspace(0, 1, 101)[1:]
    reached = [float(calls(y, p, threshold_for(p, each))[1]) for each in shares]
    threshold = float(threshold_for(p, float(share)))
    called, recall, precision = calls(y, p, threshold)
    readmitted = int(y.sum())
    caught = round(float(recall) * readmitted)
    return {
        "x": {"min": 0, "max": 1, "step": 0.1, "label": "share of stays called"},
        "y": {"min": 0, "max": 1, "step": 0.1, "label": "share of readmissions called"},
        "lines": [
            {"style": "dashed", "label": "Calling at random", "x": [0, 1], "y": [0, 1]},
            {
                "style": "main",
                "label": "Your model",
                "x": [0.0, *shares.tolist()],
                "y": [0.0, *reached],
            },
        ],
        "points": [{"x": int(called) / len(y), "y": float(recall)}],
        "readouts": [
            {"label": "Threshold", "value": f"{threshold:.3f}"},
            {"label": "Stays called", "value": f"{int(called):,} of {len(y):,}"},
            {"label": "Readmissions called", "value": f"{caught} of {readmitted}"},
            {"label": "Called stays readmitted", "value": f"{float(precision):.1%}"},
        ],
        "description": (
            f"Calling the stays at or above {threshold:.3f} calls {int(called):,} of "
            f"{len(y):,}, with {caught} of the {readmitted} readmissions among them, and "
            f"{float(precision):.1%} of the called stays readmitted."
        ),
    }
