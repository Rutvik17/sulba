import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import root_mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

# The grid strength.py chooses from.
DEGREES = [1, 2, 3]
PENALTIES = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]
# The eight measurements, in the order of the data's columns.
NAMES = ["cement", "slag", "ash", "water", "superplasticizer", "coarse", "fine", "age"]


def model(degree, penalty, rows):
    return make_pipeline(
        PolynomialFeatures(degree, include_bias=False),
        StandardScaler(),
        Ridge(alpha=penalty * rows),
    )


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, mix, y, X = table[:, 0], table[:, 1], table[:, 2], table[:, 3:]
    X_train, y_train = X[part == 0], y[part == 0]
    X_val, y_val = X[part == 1], y[part == 1]
    X_test, y_test, test_mixes = X[part == 2], y[part == 2], mix[part == 2]
    n = len(y_train)

    scores = {}
    for degree in DEGREES:
        for penalty in PENALTIES:
            fitted = model(degree, penalty, n).fit(X_train, y_train)
            scores[degree, penalty] = root_mean_squared_error(
                y_val, fitted.predict(X_val)
            )
    chosen = min(scores, key=scores.get)
    strengths = model(*chosen, n).fit(X_train, y_train).predict(X_test)

    low, high = X_train.min(axis=0), X_train.max(axis=0)
    outside = (X_test < low) | (X_test > high)
    refused = outside.any(axis=1)
    rows, columns = np.nonzero(outside)
    past = {(test_mixes[r], NAMES[c], X_test[r, c]) for r, c in zip(rows, columns)}
    value = {name: v for _, name, v in past}
    if (
        len(past) != 2
        or sorted(value) != ["coarse", "fine"]
        or len({m for m, _, _ in past}) != 2
        or np.any(X_test[outside] <= high[columns])
    ):
        raise ValueError(
            "The prose names two refused mixes, one past the top of the coarse"
            " aggregate's range and one past the top of the fine aggregate's."
        )

    def rmse(tests):
        return f"{root_mean_squared_error(y_test[tests], strengths[tests]):.2f}"

    def kg(value):
        return f"{value:,.1f}"

    return {
        "tries": str(len(scores)),
        "val_rmse": f"{scores[chosen]:.2f}",
        "test_tests": str(len(y_test)),
        "accepted": str(int(np.sum(~refused))),
        "refused": str(int(np.sum(refused))),
        "refused_mixes": str(len(np.unique(test_mixes[refused]))),
        "accepted_rmse": rmse(~refused),
        "refused_rmse": rmse(refused),
        "all_rmse": rmse(slice(None)),
        "worst": f"{np.max(np.abs(y_test - strengths)[refused]):.1f}",
        "coarse": kg(value["coarse"]),
        "coarse_top": kg(high[NAMES.index("coarse")]),
        "fine": kg(value["fine"]),
        "fine_top": kg(high[NAMES.index("fine")]),
    }
