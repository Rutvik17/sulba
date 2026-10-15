import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

THRESHOLD = 0.5
# Shares of pulsars for the table, by the name its rows use.
SHARES = {"half": 0.5, "hundred": 0.01, "thousand": 0.001}
SHUFFLES = 100


def figures():
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    model = make_pipeline(StandardScaler(), LogisticRegression())
    model.fit(table[train, 2:], table[train, 1])
    y = table[test, 1]
    scores = model.predict_proba(table[test, 2:])[:, 1]
    flagged = scores >= THRESHOLD
    found = int((flagged & (y == 1)).sum())
    tpr = found / (y == 1).sum()
    fpr = (flagged.sum() - found) / (y == 0).sum()
    rng = np.random.default_rng(0)
    shuffled = [
        average_precision_score(y, rng.permutation(len(y))) for _ in range(SHUFFLES)
    ]
    found_figures = {
        "test": f"{len(y):,}",
        "test_share": f"{y.mean():.1%}",
        "threshold": str(THRESHOLD),
        "flags": str(int(flagged.sum())),
        "tp": str(found),
        "precision": f"{found / flagged.sum():.3f}",
        "recall": f"{tpr:.3f}",
        "ap": f"{average_precision_score(y, scores):.3f}",
        "shuffles": str(SHUFFLES),
        "random_ap": f"{np.mean(shuffled):.3f}",
    }
    for name, share in SHARES.items():
        found_figures[f"share_{name}"] = f"1 in {round(1 / share):,}"
        precision = share * tpr / (share * tpr + (1 - share) * fpr)
        found_figures[f"precision_{name}"] = f"{precision:.3f}"
    return found_figures
