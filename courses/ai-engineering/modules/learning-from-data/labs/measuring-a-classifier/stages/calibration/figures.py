import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BINS = 5
# How much each training pulsar counts, against 1 for every other candidate.
WEIGHTS = [1, 2, 5, 10]


def classifier(weight=1):
    return make_pipeline(
        StandardScaler(), LogisticRegression(class_weight={0: 1, 1: weight})
    )


def figures():
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    y_train, y = table[train, 1], table[test, 1]
    found = {
        "test_pulsars": str(int(y.sum())),
        "bins": str(BINS),
        "always_brier": f"{brier_score_loss(y, np.full(len(y), y_train.mean())):.4f}",
    }
    for weight in WEIGHTS:
        model = classifier(weight).fit(table[train, 2:], y_train)
        p = model.predict_proba(table[test, 2:])[:, 1]
        found[f"weight_{weight}"] = str(weight)
        found[f"sum_{weight}"] = f"{p.sum():.1f}"
        found[f"auc_{weight}"] = f"{roc_auc_score(y, p):.3f}"
        found[f"brier_{weight}"] = f"{brier_score_loss(y, p):.4f}"
        if weight == 1:
            share, mean = calibration_curve(y, p, n_bins=BINS)
            edges = np.linspace(0, 1, BINS + 1)
            counts = np.bincount(np.searchsorted(edges[1:-1], p), minlength=BINS)
            # Every bin holds candidates, so the table has a row for each.
            assert len(share) == BINS
            # The bins between the two at the ends.
            middle = (p > edges[1]) & (p <= edges[-2])
            found["middle_count"] = str(int(middle.sum()))
            found["middle_expected"] = f"{p[middle].sum():.1f}"
            found["middle_found"] = str(int(y[middle].sum()))
            for k in range(BINS):
                found[f"from_{k}"] = f"{edges[k]:.1f}"
                found[f"to_{k}"] = f"{edges[k + 1]:.1f}"
                found[f"count_{k}"] = f"{counts[k]:,}"
                found[f"mean_{k}"] = f"{mean[k]:.3f}"
                found[f"share_{k}"] = f"{share[k]:.3f}"
    # scikit-learn's "balanced" weights: n / (2 * count) for each class.
    counts = np.bincount(y_train.astype(int))
    found["balanced"] = f"{counts[0] / counts[1]:.1f}"
    return found
