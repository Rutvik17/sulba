import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from encoding import cross_fit, encode

# The smoothing weights the chart tries, the weight it marks, and the folds and seed of the
# cross-fitting.
SMOOTHS, SMOOTH, K, SEED = range(0, 101, 10), 10, 5, 0


def chart():
    table = pd.read_csv("data/calls.csv")
    calls = table[table["set"] < 2].reset_index(drop=True)
    pairs = calls["job"] + "/" + calls["education"]
    said_yes = (calls["subscribed"] == "yes").to_numpy(dtype=int)
    splits = list(
        StratifiedKFold(K, shuffle=True, random_state=SEED).split(calls, said_yes)
    )
    own, crossed = [], []
    for smooth in SMOOTHS:
        own.append(roc_auc_score(said_yes, encode(pairs, said_yes, pairs, smooth)))
        crossed.append(
            roc_auc_score(said_yes, cross_fit(pairs, said_yes, splits, smooth))
        )
    weights = list(SMOOTHS)
    at = weights.index(SMOOTH)
    return {
        "x": {
            "min": weights[0],
            "max": weights[-1],
            "step": 10,
            "label": "smoothing weight m",
        },
        "y": {"min": 0.5, "max": 0.7, "step": 0.05, "label": "AUC"},
        "lines": [
            {
                "style": "faint",
                "label": "Learnt with each call's own answer",
                "x": weights,
                "y": [round(float(auc), 6) for auc in own],
            },
            {
                "style": "main",
                "label": "Cross-fitted",
                "x": weights,
                "y": [round(float(auc), 6) for auc in crossed],
            },
        ],
        "points": [{"x": SMOOTH, "y": round(float(crossed[at]), 6)}],
        "readouts": [
            {
                "label": f"AUC learnt with each call's own answer, m = {SMOOTH}",
                "value": f"{own[at]:.3f}",
            },
            {"label": f"AUC cross-fitted, m = {SMOOTH}", "value": f"{crossed[at]:.3f}"},
        ],
        "description": (
            f"The AUC of the {len(calls):,} calls ranked by their job and education pair's "
            f"encoding, for smoothing weights from {weights[0]} to {weights[-1]}. Learnt with "
            f"each call's own answer, it falls from {own[0]:.3f} to {own[-1]:.3f}; "
            f"cross-fitted, it runs from {crossed[0]:.3f} to {crossed[-1]:.3f}."
        ),
    }
