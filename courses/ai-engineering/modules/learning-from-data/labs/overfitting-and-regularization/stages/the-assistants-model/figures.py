import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

# The assistant's grid, as strength.py has it.
DEGREES = [1, 2, 3]
PENALTIES = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]


def model(degree, alpha):
    return make_pipeline(
        PolynomialFeatures(degree, include_bias=False),
        StandardScaler(),
        Ridge(alpha=alpha),
    )


def penalty_text(penalty):
    return np.format_float_positional(penalty, trim="-")


def best(scores):
    return min(scores, key=scores.get)


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, mix, y, X = table[:, 0], table[:, 1], table[:, 2], table[:, 3:]
    X_train, y_train = X[part == 0], y[part == 0]
    X_val, y_val, X_test = X[part == 1], y[part == 1], X[part == 2]
    n = len(y_train)

    # Each pair fit on the training tests with the penalty scaled, and with it as given.
    train_scores, val_scores, unscaled_train = {}, {}, {}
    for degree in DEGREES:
        for penalty in PENALTIES:
            fitted = model(degree, n * penalty).fit(X_train, y_train)
            train_scores[degree, penalty] = root_mean_squared_error(
                y_train, fitted.predict(X_train)
            )
            val_scores[degree, penalty] = root_mean_squared_error(
                y_val, fitted.predict(X_val)
            )
            weak = model(degree, penalty).fit(X_train, y_train)
            unscaled_train[degree, penalty] = root_mean_squared_error(
                y_train, weak.predict(X_train)
            )
    chosen, by_training = best(val_scores), best(train_scores)
    scaled = model(*chosen[:1], n * chosen[1]).fit(X_train, y_train).predict(X_test)
    weak = model(*chosen[:1], chosen[1]).fit(X_train, y_train).predict(X_test)

    # The plant's records, the training and validation tests, with a fifth held out.
    records = (part == 0) | (part == 1)
    X_all, y_all, mixes = X[records], y[records], mix[records]
    tests = np.arange(len(y_all))
    fit_rows, held_rows = train_test_split(tests, test_size=0.2, random_state=0)
    groups = GroupShuffleSplit(test_size=0.2, random_state=0)
    fit_mixes, held_mixes = next(groups.split(tests, groups=mixes))

    def error(fit, held, alpha_per_test=True, fit_all=False):
        degree, penalty = chosen
        rows = tests if fit_all else fit
        alpha = penalty * len(rows) if alpha_per_test else penalty
        fitted = model(degree, alpha).fit(X_all[rows], y_all[rows])
        return root_mean_squared_error(y_all[held], fitted.predict(X_all[held]))

    # What the assistant's code would have said: its own choice, by training error with the
    # penalty unscaled, scored with all four problems.
    told_degree, told_penalty = best(unscaled_train)
    told = model(told_degree, told_penalty).fit(X_all, y_all)
    return {
        "n": str(n),
        "alpha_gap": f"{np.max(np.abs(scaled - weak)):.1f}",
        "best_degree": str(chosen[0]),
        "best_penalty": penalty_text(chosen[1]),
        "best_val": f"{val_scores[chosen]:.2f}",
        "train_degree": str(by_training[0]),
        "train_penalty": penalty_text(by_training[1]),
        "train_choice_val": f"{val_scores[by_training]:.2f}",
        "held": str(len(held_rows)),
        "twins": str(int(np.isin(mixes[held_rows], mixes[fit_rows]).sum())),
        "row_error": f"{error(fit_rows, held_rows):.2f}",
        "mix_error": f"{error(fit_mixes, held_mixes):.2f}",
        "seen_error": f"{error(fit_mixes, held_mixes, fit_all=True):.2f}",
        "told": f"{root_mean_squared_error(y_all[held_rows], told.predict(X_all[held_rows])):.2f}",
    }
