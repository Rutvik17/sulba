"""Comparing the bank's models: the same folds for every model, and error bars on their
differences."""

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from scipy.stats import t
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

# The columns the models read of each call: these numbers, and a column for each category
# of these.
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
# The model the others are compared with.
BASELINE = "logistic regression"


def columns(scale):
    """The calls' columns as a model reads them: the numbers, standardized if scale, and a
    column of 1s and 0s for each category."""
    numbers = StandardScaler() if scale else "passthrough"
    categories = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return ColumnTransformer(
        [("numbers", numbers, NUMBERS), ("categories", categories, CATEGORIES)]
    ).set_output(transform="pandas")


def models():
    """The baseline, then the four models compared with it, each a pipeline from the calls
    to a chance of yes."""
    return {
        BASELINE: make_pipeline(columns(True), LogisticRegression(max_iter=1000)),
        "nearest neighbours": make_pipeline(
            columns(True),
            KNeighborsClassifier(50, metric="manhattan", algorithm="brute"),
        ),
        "decision tree": make_pipeline(
            columns(False), DecisionTreeClassifier(min_samples_leaf=50, random_state=0)
        ),
        "random forest": make_pipeline(
            columns(False),
            RandomForestClassifier(100, min_samples_leaf=10, random_state=0),
        ),
        "gradient boosting": make_pipeline(
            columns(False),
            LGBMClassifier(
                n_estimators=100,
                learning_rate=0.05,
                num_leaves=8,
                n_jobs=1,
                verbose=-1,
                random_state=0,
            ),
        ),
    }


def fold_scores(models, calls, said_yes, splits):
    """Each model's AUC on the held calls of each split, fitted afresh on its fit calls: a
    row per split and a column per model."""
    table = {name: [] for name in models}
    for fit, held in splits:
        for name, model in models.items():
            fitted = clone(model).fit(calls.iloc[fit], said_yes[fit])
            chances = fitted.predict_proba(calls.iloc[held])[:, 1]
            table[name].append(roc_auc_score(said_yes[held], chances))
    return pd.DataFrame(table)


def differences(scores, baseline):
    """Each other model's AUC less the baseline's, split by split."""
    return scores.drop(columns=baseline).sub(scores[baseline], axis=0)


def corrected_se(differences, n_fit, n_held):
    """The standard error of the mean of differences between two models' AUCs on folds of
    n_fit calls fitted on and n_held held out, allowing for the calls the folds share."""
    n = len(differences)
    return float(np.sqrt(np.var(differences, ddof=1) * (1 / n + n_held / n_fit)))


def interval(differences, n_fit, n_held, confidence):
    """The interval around the mean difference at this confidence, from the t distribution
    and the corrected standard error."""
    quantile = t.ppf((1 + confidence) / 2, len(differences) - 1)
    half = quantile * corrected_se(differences, n_fit, n_held)
    mean = float(np.mean(differences))
    return mean - half, mean + half
