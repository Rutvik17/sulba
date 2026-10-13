import math

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def at_most(value):
    """value rounded up at 4 decimal places, so a bound such as "up to" stays true."""
    return f"{math.ceil(value * 10_000) / 10_000:.4f}"


def sigmoid(z):
    return np.exp(-np.logaddexp(0.0, -z))


def figures():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, y_train, X_test = X[~test], y[~test], X[test]
    scaler = StandardScaler().fit(X_train)
    X_train_scaled, X_test_scaled = scaler.transform(X_train), scaler.transform(X_test)

    # Your model, trained as in stage 3: gradient descent from zero, lr 4, 1,000 steps.
    w, b, l2 = np.zeros(X.shape[1]), 0.0, 1 / len(y_train)
    for _ in range(1_000):
        error = sigmoid(X_train_scaled @ w + b) - y_train
        w = w - 4.0 * (X_train_scaled.T @ error / len(y_train) + l2 * w)
        b = b - 4.0 * float(np.mean(error))
    yours = sigmoid(X_test_scaled @ w + b)

    default = LogisticRegression().fit(X_train_scaled, y_train)
    balanced = LogisticRegression(class_weight="balanced").fit(X_train_scaled, y_train)
    p_default = default.predict_proba(X_test_scaled)[:, 1]
    p_balanced = balanced.predict_proba(X_test_scaled)[:, 1]
    # The test set scaled with its own means and standard deviations, as fit_transform does.
    p_skewed = default.predict_proba(StandardScaler().fit_transform(X_test))[:, 1]
    # A lone sample scaled with its own numbers is all zeros.
    lone = default.predict_proba(np.zeros((1, X.shape[1])))[0, 1]

    return {
        "lone_score": f"{lone:.4f}",
        "skew_gap": at_most(np.max(np.abs(p_skewed - p_default))),
        "weights_gap": at_most(np.max(np.abs(p_balanced - p_default))),
        "your_model_gap": at_most(np.max(np.abs(p_default - yours))),
    }
