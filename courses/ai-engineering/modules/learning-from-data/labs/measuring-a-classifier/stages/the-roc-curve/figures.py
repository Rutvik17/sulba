import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

THRESHOLD = 0.5


def figures():
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    model = make_pipeline(StandardScaler(), LogisticRegression())
    model.fit(table[train, 2:], table[train, 1])
    y = table[test, 1]
    scores = model.predict_proba(table[test, 2:])[:, 1]
    pulsars, others = scores[y == 1], scores[y == 0]
    # Each pulsar against each other candidate: the share it outranks, ties counting half.
    above = (pulsars[:, None] > others[None, :]).sum()
    tied = (pulsars[:, None] == others[None, :]).sum()
    pairs = len(pulsars) * len(others)
    share = (above + tied / 2) / pairs
    # The share of pairs in the right order is the area under the ROC curve.
    assert abs(share - roc_auc_score(y, scores)) < 1e-12
    flagged = scores >= THRESHOLD
    found = int((flagged & (y == 1)).sum())
    false = int((flagged & (y == 0)).sum())
    return {
        "train": f"{int(train.sum()):,}",
        "test": f"{int(test.sum()):,}",
        "test_pulsars": str(len(pulsars)),
        "test_others": f"{len(others):,}",
        "pairs": f"{pairs:,}",
        "share_right": f"{share:.1%}",
        "auc": f"{share:.3f}",
        "threshold": str(THRESHOLD),
        "tp": str(found),
        "fp": str(false),
        "tpr": f"{found / len(pulsars):.3f}",
        "fpr": f"{false / len(others):.4f}",
        "accuracy": f"{np.mean(flagged == (y == 1)):.1%}",
        "always_no": f"{np.mean(y == 0):.1%}",
    }
