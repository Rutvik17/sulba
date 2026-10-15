import numpy as np
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SHARE = 0.02
THRESHOLD = 0.5
FOLLOW_UPS = 500


def log_odds(share):
    return np.log(share / (1 - share))


def figures():
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    train = table[:, 0] == 0
    y_train = table[train, 1]
    model = make_pipeline(StandardScaler(), LogisticRegression())
    model.fit(table[train, 2:], y_train)
    # The checks' candidates: every other candidate of the validation and test sets, and
    # pulsars drawn from them to make 1 in 50.
    unseen = table[table[:, 0] > 0]
    others = np.flatnonzero(unseen[:, 1] == 0)
    count = round(len(others) * SHARE / (1 - SHARE))
    pulsars = np.random.default_rng(0).choice(
        np.flatnonzero(unseen[:, 1] == 1), count, replace=False
    )
    rows = np.sort(np.concatenate([others, pulsars]))
    X, y = unseen[rows, 2:], unseen[rows, 1]
    shift = log_odds(SHARE) - log_odds(y_train.mean())
    own = model.predict_proba(X)[:, 1]
    adjusted = expit(model.decision_function(X) + shift)
    own_flags, adjusted_flags = own >= THRESHOLD, adjusted >= THRESHOLD
    return {
        "one_in": f"1 in {round(1 / SHARE)}",
        "train_share": f"{y_train.mean():.1%}",
        "odds_factor": f"{np.exp(shift):.3f}",
        "drawn": f"{len(y):,}",
        "drawn_pulsars": str(int(y.sum())),
        "own_sum": f"{own.sum():.1f}",
        "adjusted_sum": f"{adjusted.sum():.1f}",
        "threshold": str(THRESHOLD),
        "own_flags": str(int(own_flags.sum())),
        "own_precision": f"{y[own_flags].mean():.1%}",
        "adjusted_flags": str(int(adjusted_flags.sum())),
        "adjusted_precision": f"{y[adjusted_flags].mean():.1%}",
        "follow_ups": str(FOLLOW_UPS),
        "night": f"{100_000:,}",
    }
