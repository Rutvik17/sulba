import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

THRESHOLD = 0.5


def fitted(X, y, weight=None):
    model = make_pipeline(StandardScaler(), LogisticRegression(class_weight=weight))
    return model.fit(X, y)


def balanced_sample(y):
    """The assistant's sample: every pulsar, and as many other candidates at random."""
    rng = np.random.default_rng(0)
    pulsars = np.flatnonzero(y == 1)
    others = rng.choice(np.flatnonzero(y == 0), len(pulsars), replace=False)
    return np.sort(np.concatenate([pulsars, others]))


def figures():
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train, test = table[:, 0] == 0, table[:, 0] == 2
    X_train, y_train = table[train, 2:], table[train, 1]
    X, y = table[test, 2:], table[test, 1]
    plain = fitted(X_train, y_train)
    weighted = fitted(X_train, y_train, "balanced")
    p, q = plain.predict_proba(X)[:, 1], weighted.predict_proba(X)[:, 1]
    rows = balanced_sample(y)
    flagged = p >= THRESHOLD
    sample_flagged = p[rows] >= THRESHOLD
    counts = np.bincount(y_train.astype(int))
    # What the assistant's report says with all four problems in it.
    told = {
        "auc": roc_auc_score(y[rows], weighted.predict(X[rows])),
        "precision": y[rows][q[rows] >= THRESHOLD].mean(),
        "expected": int((q >= THRESHOLD).sum()),
    }
    return {
        "threshold": str(THRESHOLD),
        "test": f"{len(y):,}",
        "pulsars": str(int(y.sum())),
        "test_share": f"{y.mean():.1%}",
        "balanced": f"{counts[0] / counts[1]:.1f}",
        "plain_sum": f"{p.sum():.1f}",
        "weighted_sum": f"{q.sum():.1f}",
        "times_over": f"{q.sum() / y.sum():.1f}",
        "sample": str(len(rows)),
        "sample_precision": f"{y[rows][sample_flagged].mean():.3f}",
        "precision": f"{y[flagged].mean():.3f}",
        "auc": f"{roc_auc_score(y, p):.3f}",
        "hard_auc": f"{roc_auc_score(y, flagged):.3f}",
        "tpr": f"{flagged[y == 1].mean():.3f}",
        "tnr": f"{1 - flagged[y == 0].mean():.3f}",
        "flags": str(int(flagged.sum())),
        "below": f"{int((~flagged).sum()):,}",
        "missed": str(int(y[~flagged].sum())),
        "false": str(int((flagged & (y == 0)).sum())),
        "told_auc": f"{told['auc']:.3f}",
        "told_precision": f"{told['precision']:.3f}",
        "told_expected": str(told["expected"]),
    }
