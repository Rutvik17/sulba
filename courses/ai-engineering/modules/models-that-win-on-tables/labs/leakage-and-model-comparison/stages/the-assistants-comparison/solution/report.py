"""The bank's comparison of its models: the baseline and the module's four models, each
reading the share of yes of a call's age and of its job and education, scored on the same
folds, with an interval for each model's difference from the baseline."""

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from scipy.stats import t
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, TargetEncoder
from sklearn.tree import DecisionTreeClassifier

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
# The columns whose share of yes the models read, and the names of the shares.
ENCODED = ["age", "pair"]
SHARES = ["age share", "pair share"]
# The folds and their shuffles, the seed, the shares' smoothing weight, and the
# confidence of the intervals.
K, REPEATS, SEED, SMOOTH, CONFIDENCE = 5, 5, 0, 10, 0.95
BASELINE = "logistic regression"


def with_pairs(calls):
    """The calls with a pair column: each call's job and education, as job/education."""
    return calls.assign(pair=calls["job"] + "/" + calls["education"])


def columns(scale):
    """The columns a model reads: the numbers and the shares, standardized if scale, and
    a column of 1s and 0s for each category."""
    numbers = StandardScaler() if scale else "passthrough"
    categories = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return ColumnTransformer(
        [("numbers", numbers, NUMBERS + SHARES), ("categories", categories, CATEGORIES)]
    ).set_output(transform="pandas")


def models():
    """The baseline, then the four models compared with it."""
    return {
        BASELINE: make_pipeline(columns(True), LogisticRegression(max_iter=1000)),
        "nearest neighbours": make_pipeline(
            columns(True),
            KNeighborsClassifier(50, metric="manhattan", algorithm="brute"),
        ),
        "decision tree": make_pipeline(
            columns(False),
            DecisionTreeClassifier(min_samples_leaf=50, random_state=SEED),
        ),
        "random forest": make_pipeline(
            columns(False),
            RandomForestClassifier(100, min_samples_leaf=10, random_state=SEED),
        ),
        "gradient boosting": make_pipeline(
            columns(False),
            LGBMClassifier(
                n_estimators=100,
                learning_rate=0.05,
                num_leaves=8,
                n_jobs=1,
                verbose=-1,
                random_state=SEED,
            ),
        ),
    }


def folds(calls, said_yes, repeats):
    """repeats shuffles of K stratified folds of the calls, as (fit, held) row numbers."""
    shuffles = RepeatedStratifiedKFold(n_splits=K, n_repeats=repeats, random_state=SEED)
    return list(shuffles.split(calls, said_yes))


def shares(calls, said_yes, fit, held):
    """The fit calls and the held calls, each with the shares of its age and its pair,
    learnt on the fit calls."""
    encoder = TargetEncoder(smooth=SMOOTH, target_type="binary", random_state=SEED)
    fit_shares = encoder.fit_transform(calls.iloc[fit][ENCODED], said_yes[fit])
    held_shares = encoder.transform(calls.iloc[held][ENCODED])
    return (
        calls.iloc[fit].assign(**dict(zip(SHARES, fit_shares.T, strict=True))),
        calls.iloc[held].assign(**dict(zip(SHARES, held_shares.T, strict=True))),
    )


def fold_scores(models, calls, said_yes, repeats=REPEATS):
    """Each model's AUC on the held calls of each fold of repeats shuffles: a row per
    fold."""
    table = {}
    for name, model in models.items():
        aucs = []
        for fit, held in folds(calls, said_yes, repeats):
            fit_calls, held_calls = shares(calls, said_yes, fit, held)
            fitted = clone(model).fit(fit_calls, said_yes[fit])
            chances = fitted.predict_proba(held_calls)[:, 1]
            aucs.append(roc_auc_score(said_yes[held], chances))
        table[name] = aucs
    return pd.DataFrame(table)


def standard_error(differences, n_fit, n_held):
    """The standard error of the mean of differences between two models' AUCs on folds
    of n_fit calls fitted on and n_held held out."""
    n = len(differences)
    return float(np.sqrt(np.var(differences, ddof=1) * (1 / n + n_held / n_fit)))


def interval(differences, n_fit, n_held, confidence):
    """The interval around the mean difference at this confidence."""
    quantile = t.ppf((1 + confidence) / 2, len(differences) - 1)
    half = quantile * standard_error(differences, n_fit, n_held)
    mean = float(np.mean(differences))
    return mean - half, mean + half


def run(calls, said_yes):
    """Each model's mean AUC, and each other model's mean difference from the baseline
    with its interval: a row per model."""
    calls = with_pairs(calls)
    scores = fold_scores(models(), calls, said_yes)
    fit, held = folds(calls, said_yes, REPEATS)[0]
    rows = []
    for name in scores.columns:
        difference = scores[name] - scores[BASELINE]
        low, high = (np.nan, np.nan)
        if name != BASELINE:
            low, high = interval(difference, len(fit), len(held), CONFIDENCE)
        rows.append(
            {
                "model": name,
                "auc": scores[name].mean(),
                "difference": difference.mean(),
                "low": low,
                "high": high,
            }
        )
    return pd.DataFrame(rows).set_index("model")
