import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, TargetEncoder

NUMBERS = ["age", "campaign", "pdays", "previous"]
CATEGORIES = [
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "poutcome",
]
# The smoothing weight, the chart's largest, a rare pair's most calls, and the folds of the
# baseline's cross-validation.
SMOOTH, MOST, RARE, K, REPEATS, SEED = 10, 100, 10, 5, 5, 0


def encode(fit_values, fit_yes, values, smooth):
    prior = np.mean(fit_yes)
    groups = pd.Series(fit_yes).groupby(fit_values.to_numpy())
    shares = (groups.sum() + smooth * prior) / (groups.count() + smooth)
    return values.map(shares).fillna(prior).to_numpy(dtype=float)


def cross_fit(values, said_yes, splits, smooth):
    encoded = np.empty(len(values))
    for fit, held in splits:
        encoded[held] = encode(
            values.iloc[fit], said_yes[fit], values.iloc[held], smooth
        )
    return encoded


def baseline(extra):
    """The logistic regression on the client columns, with extra columns as numbers."""
    columns = ColumnTransformer(
        [
            ("numbers", StandardScaler(), NUMBERS + extra),
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORIES,
            ),
        ]
    )
    return make_pipeline(columns, LogisticRegression(max_iter=1000))


def inside():
    """The baseline with the pair encoded inside each fold, cross-fitted on its fit calls."""
    encoder = make_pipeline(
        TargetEncoder(smooth=SMOOTH, target_type="binary", random_state=SEED),
        StandardScaler(),
    )
    columns = ColumnTransformer(
        [
            ("numbers", StandardScaler(), NUMBERS),
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORIES,
            ),
            ("pair", encoder, ["pair"]),
        ]
    )
    return make_pipeline(columns, LogisticRegression(max_iter=1000))


def mean_auc(model, calls, said_yes, splits):
    aucs = []
    for fit, held in splits:
        fitted = clone(model).fit(calls.iloc[fit], said_yes[fit])
        aucs.append(
            roc_auc_score(said_yes[held], fitted.predict_proba(calls.iloc[held])[:, 1])
        )
    return np.mean(aucs)


def figures():
    table = pd.read_csv("data/calls.csv")
    calls = table[table["set"] < 2].reset_index(drop=True)
    calls = calls.assign(pair=calls["job"] + "/" + calls["education"])
    said_yes = (calls["subscribed"] == "yes").to_numpy(dtype=int)
    counts = calls["pair"].value_counts()
    yes = pd.Series(said_yes).groupby(calls["pair"].to_numpy()).sum()
    # The explanation's rare pair: the one with the fewest calls, at least one of them yes.
    held_yes = counts[yes[counts.index].to_numpy() > 0]
    example = held_yes.index[np.argmin(held_yes.to_numpy())]
    n, y = int(counts[example]), int(yes[example])
    # The explanation describes a pair of a single call, which said yes.
    assert (n, y) == (1, 1)
    prior = said_yes.mean()
    splits = list(
        StratifiedKFold(K, shuffle=True, random_state=SEED).split(calls, said_yes)
    )

    def aucs(smooth):
        own = encode(calls["pair"], said_yes, calls["pair"], smooth)
        crossed = cross_fit(calls["pair"], said_yes, splits, smooth)
        return roc_auc_score(said_yes, own), roc_auc_score(said_yes, crossed)

    own, crossed = aucs(SMOOTH)
    own_most, crossed_most = aucs(MOST)
    folds = list(
        RepeatedStratifiedKFold(n_splits=K, n_repeats=REPEATS, random_state=SEED).split(
            calls, said_yes
        )
    )
    leaked = calls.assign(share=encode(calls["pair"], said_yes, calls["pair"], SMOOTH))
    return {
        "calls": f"{len(calls):,}",
        "pairs": str(len(counts)),
        "top_pair": str(counts.index[0]),
        "top_calls": str(counts.iloc[0]),
        "rare": str(int((counts < RARE).sum())),
        "rare_calls": str(RARE),
        "example": str(example),
        "example_yes": f"{(1 + SMOOTH * prior) / (n + SMOOTH):.3f}",
        "example_no": f"{SMOOTH * prior / (n + SMOOTH):.3f}",
        "example_move": f"{1 / (n + SMOOTH):.3f}",
        "smooth": str(SMOOTH),
        "most": str(MOST),
        "own_auc": f"{own:.3f}",
        "crossed_auc": f"{crossed:.3f}",
        "own_most": f"{own_most:.3f}",
        "crossed_most": f"{crossed_most:.3f}",
        "folds": str(K * REPEATS),
        "baseline": f"{mean_auc(baseline([]), calls, said_yes, folds):.4f}",
        "inside": f"{mean_auc(inside(), calls, said_yes, folds):.4f}",
        "leaked": f"{mean_auc(baseline(['share']), leaked, said_yes, folds):.4f}",
    }
