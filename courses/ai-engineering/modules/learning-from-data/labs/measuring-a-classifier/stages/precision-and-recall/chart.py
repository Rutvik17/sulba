import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from metrics import average_precision, pr_curve, precision_at, roc_curve

THRESHOLD = 0.5


def arrays(parts):
    return tuple(np.asarray(part, dtype=float) for part in parts)


def chart(share):
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    model = make_pipeline(StandardScaler(), LogisticRegression())
    model.fit(table[train, 2:], table[train, 1])
    y = table[test, 1]
    scores = model.predict_proba(table[test, 2:])[:, 1]
    one_in = f"1 pulsar in {round(1 / share):,}"

    # The threshold's rates, on your ROC curve.
    fpr, tpr, thresholds = arrays(roc_curve(y, scores))
    at = np.flatnonzero(thresholds >= THRESHOLD)[-1]
    on_test = float(precision_at(y.mean(), tpr[at], fpr[at]))
    at_share = float(precision_at(share, tpr[at], fpr[at]))
    # Drawn from the scores to four places, which every runtime orders the same way.
    precision, recall, _ = arrays(pr_curve(y, np.round(scores, 4)))
    drawn_fpr, drawn_tpr, _ = arrays(roc_curve(y, np.round(scores, 4)))
    shifted = np.asarray(precision_at(share, drawn_tpr[1:], drawn_fpr[1:]), dtype=float)

    return {
        "x": {"min": 0, "max": 1, "step": 0.1, "label": "recall"},
        "y": {"min": 0, "max": 1, "step": 0.1, "label": "precision"},
        "lines": [
            {
                "style": "base",
                "label": f"Test set, {y.mean():.1%} pulsars",
                "x": recall,
                "y": precision,
            },
            {
                "style": "main",
                "label": one_in,
                "x": drawn_tpr[1:],
                "y": shifted,
            },
        ],
        "points": [{"x": round(tpr[at], 6), "y": round(at_share, 6)}],
        "readouts": [
            {
                "label": "Average precision, test set",
                "value": f"{average_precision(y, scores):.3f}",
            },
            {
                "label": f"Precision at {THRESHOLD:g}, test set",
                "value": f"{on_test:.3f}",
            },
            {
                "label": f"Precision at {THRESHOLD:g}, {one_in}",
                "value": f"{at_share:.3f}",
            },
        ],
        "description": (
            f"Your precision against recall for the {len(y):,} test candidates, "
            f"{y.mean():.1%} of them pulsars, and at the same thresholds with {one_in} "
            f"candidates. At a threshold of {THRESHOLD:g}, precision is "
            f"{on_test:.3f} on the test set and {at_share:.3f} at {one_in}."
        ),
    }
