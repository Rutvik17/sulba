import math

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def figures():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, y_train, X_test, y_test = X[~test], y[~test], X[test], y[test]
    # The fixed screener's probabilities for the test set.
    scaler = StandardScaler().fit(X_train)
    model = LogisticRegression().fit(scaler.transform(X_train), y_train)
    p = model.predict_proba(scaler.transform(X_test))[:, 1]
    malignant = y_test == 1

    sent = p >= 0.5
    tp = int(np.sum(sent & malignant))
    fp = int(np.sum(sent & ~malignant))
    fn = int(np.sum(~sent & malignant))
    tn = int(np.sum(~sent & ~malignant))

    # A recall of 0.98: the threshold is the k-th highest malignant probability.
    positives = int(np.sum(malignant))
    k = math.ceil(0.98 * positives)
    threshold = np.sort(p[malignant])[::-1][k - 1]
    if k != positives:
        raise ValueError(
            "The prose calls the threshold the lowest malignant probability."
        )
    sent_at = p >= threshold
    found = int(np.sum(sent_at & malignant))

    return {
        "tp": str(tp),
        "fp": str(fp),
        "fn": str(fn),
        "tn": str(tn),
        "precision": f"{tp / (tp + fp):.4f}",
        "recall": f"{tp / (tp + fn):.4f}",
        "positives": str(positives),
        "r_times_p": f"{0.98 * positives:.2f}",
        "k": str(k),
        "threshold": f"{threshold:.4f}",
        "sent": str(int(np.sum(sent_at))),
        "extra": str(int(np.sum(sent_at & ~malignant))),
        "precision_at_threshold": f"{found / int(np.sum(sent_at)):.4f}",
    }
