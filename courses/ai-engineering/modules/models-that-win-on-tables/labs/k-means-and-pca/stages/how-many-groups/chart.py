import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from groups import MEASUREMENTS, scale, silhouette

# The numbers of groups the chart tries, the k-means++ starts each takes the best of, and the
# seed of the starts.
KS, STARTS, SEED = range(2, 11), 10, 0


def chart():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0]
    measured = train[MEASUREMENTS].to_numpy(dtype=float)
    Z, _ = scale(measured, measured)
    varieties = train["variety"].to_numpy()
    scores, shares = [], []
    for k in KS:
        labels = KMeans(k, n_init=STARTS, random_state=SEED).fit(Z).labels_
        scores.append(silhouette(Z, labels))
        commonest = sum(
            pd.Series(varieties[labels == group]).value_counts().iloc[0]
            for group in range(k)
        )
        shares.append(commonest / len(Z))
    best = int(np.argmax(scores))
    ks = list(KS)
    return {
        "x": {"min": ks[0], "max": ks[-1], "step": 1, "label": "groups"},
        "y": {"min": 0, "max": 1, "step": 0.2, "label": "silhouette or share"},
        "lines": [
            {
                "style": "faint",
                "label": "Beans in their group's commonest variety",
                "x": ks,
                "y": [round(float(share), 6) for share in shares],
            },
            {
                "style": "main",
                "label": "Silhouette",
                "x": ks,
                "y": [round(float(score), 6) for score in scores],
            },
        ],
        "points": [{"x": ks[best], "y": round(float(scores[best]), 6)}],
        "readouts": [
            {"label": "Groups with the highest silhouette", "value": str(ks[best])},
            {"label": "Its silhouette", "value": f"{scores[best]:.3f}"},
        ],
        "description": (
            f"The mean silhouette of the {len(Z):,} training beans in {ks[0]} to {ks[-1]} "
            f"groups, each the best of {STARTS} k-means++ starts, beside the share of beans in "
            f"their group's commonest variety. The silhouette is highest at {ks[best]} groups, "
            f"{scores[best]:.3f}; the share rises from {shares[0]:.1%} at {ks[0]} groups to "
            f"{shares[-1]:.1%} at {ks[-1]}."
        ),
    }
