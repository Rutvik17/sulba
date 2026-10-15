import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from metrics import brier, reliability

BINS = 5


def chart(weight):
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    model = make_pipeline(
        StandardScaler(), LogisticRegression(class_weight={0: 1, 1: weight})
    )
    model.fit(table[train, 2:], table[train, 1])
    y = table[test, 1]
    p = model.predict_proba(table[test, 2:])[:, 1]
    share, mean = (np.asarray(part, dtype=float) for part in reliability(y, p, BINS))
    # Probabilities to six places, which every runtime gives the same.
    share, mean = np.round(share, 6), np.round(mean, 6)
    expected = float(np.sum(p))

    return {
        "x": {"min": 0, "max": 1, "step": 0.1, "label": "mean probability in the bin"},
        "y": {"min": 0, "max": 1, "step": 0.1, "label": "share of pulsars in the bin"},
        "lines": [
            {"style": "dashed", "label": "Calibrated", "x": [0, 1], "y": [0, 1]},
            {"style": "main", "label": "Your reliability", "x": mean, "y": share},
        ],
        "points": [{"x": x, "y": s} for x, s in zip(mean, share, strict=True)],
        "readouts": [
            {"label": "Pulsars expected", "value": f"{expected:.1f}"},
            {"label": "Pulsars in the test set", "value": str(int(y.sum()))},
            {"label": "Brier score", "value": f"{brier(y, p):.4f}"},
        ],
        "description": (
            f"Your reliability in {BINS} bins, with each training pulsar weighted "
            f"{weight:g}: the probabilities for the {len(y):,} test "
            f"candidates add up to {expected:.1f}, for {int(y.sum())} pulsars, with a "
            f"Brier score of {brier(y, p):.4f}."
        ),
    }
