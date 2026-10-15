import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from metrics import roc_auc, roc_curve


def chart(threshold):
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    model = make_pipeline(StandardScaler(), LogisticRegression())
    model.fit(table[train, 2:], table[train, 1])
    y = table[test, 1]
    scores = model.predict_proba(table[test, 2:])[:, 1]
    pulsars, others = int(y.sum()), int((y == 0).sum())

    # The point at the threshold, on your curve: the lowest threshold at or above it.
    fpr, tpr, thresholds = (
        np.asarray(part, dtype=float) for part in roc_curve(y, scores)
    )
    at = np.flatnonzero(thresholds >= threshold)[-1]
    found, false = round(tpr[at] * pulsars), round(fpr[at] * others)
    # Drawn from the scores to four places, which every runtime orders the same way.
    drawn_fpr, drawn_tpr, _ = (
        np.asarray(part, dtype=float) for part in roc_curve(y, np.round(scores, 4))
    )
    auc = roc_auc(y, scores)

    return {
        "x": {"min": 0, "max": 1, "step": 0.1, "label": "false positive rate"},
        "y": {"min": 0, "max": 1, "step": 0.1, "label": "true positive rate"},
        "lines": [
            {"style": "dashed", "label": "Random order", "x": [0, 1], "y": [0, 1]},
            {
                "style": "main",
                "label": "Your ROC curve",
                "x": drawn_fpr,
                "y": drawn_tpr,
            },
        ],
        "points": [{"x": round(fpr[at], 6), "y": round(tpr[at], 6)}],
        "readouts": [
            {
                "label": f"Pulsars flagged at {threshold:g}",
                "value": f"{found} of {pulsars}",
            },
            {"label": "Others flagged", "value": f"{false} of {others:,}"},
            {"label": "AUC", "value": f"{auc:.3f}"},
        ],
        "description": (
            f"Your ROC curve for the {len(y):,} test candidates, with an AUC of {auc:.3f}. "
            f"At a threshold of {threshold:g} it flags {found} of the {pulsars} pulsars "
            f"and {false} of the {others:,} other candidates."
        ),
    }
