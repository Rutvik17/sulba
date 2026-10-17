"""The readmission model: its pipeline, and the scores it's judged by."""

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from features import CATEGORIES, COUNTS, features

SEED = 0


def make_model():
    """A new, unfitted pipeline: the counts and age scaled, the categories one-hot encoded,
    and a logistic regression."""
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    return make_pipeline(encode, LogisticRegression(max_iter=1000))


def held_out(table):
    """The stays split at random into a part to learn from and 30% held out, each with the
    same share readmitted."""
    return train_test_split(
        table, test_size=0.3, random_state=SEED, stratify=table["readmitted"]
    )


def scores(model, learn, test):
    """The model fitted to learn's stays, and its probability of a readmission for each of
    test's."""
    model.fit(features(learn), learn["readmitted"])
    return model.predict_proba(features(test))[:, 1]


def auc(test, probabilities):
    """How well the probabilities rank test's stays: the area under the ROC curve."""
    return roc_auc_score(test["readmitted"], probabilities)


def baseline(test):
    """The AUC of ranking test's stays by their inpatient visits in the year before."""
    return auc(test, test["number_inpatient"])


def cross_validated(table, make=make_model, folds=5):
    """Each fold's AUC: a new model from make() fitted to the other folds' stays and scored
    on the fold's, with the folds stratified by readmitted and shuffled with SEED."""
    splitter = StratifiedKFold(folds, shuffle=True, random_state=SEED)
    aucs = []
    for learn, test in splitter.split(table, table["readmitted"]):
        learn, test = table.iloc[learn], table.iloc[test]
        aucs.append(auc(test, scores(make(), learn, test)))
    return aucs


def summary(aucs):
    """The mean of the AUCs, and its standard error: their standard deviation over the square
    root of how many there are."""
    aucs = np.asarray(aucs, dtype=float)
    return float(aucs.mean()), float(aucs.std(ddof=1) / np.sqrt(len(aucs)))


def out_of_fold(table, make=make_model, folds=5):
    """Each stay's probability of a readmission from the fold model, made by make(), that
    didn't learn from it, in the order of table's rows, over the folds cross_validated uses."""
    splitter = StratifiedKFold(folds, shuffle=True, random_state=SEED)
    probabilities = np.empty(len(table))
    for learn, test in splitter.split(table, table["readmitted"]):
        probabilities[test] = scores(make(), table.iloc[learn], table.iloc[test])
    return probabilities


def calibration(y, probabilities, bins=10):
    """For bins groups of stays ranked by probability, each about as large as the others,
    each group's mean probability and the share of it readmitted, as (predicted, observed)."""
    p = np.asarray(probabilities, dtype=float)
    edges = np.quantile(p, np.linspace(0, 1, bins + 1))
    group = np.searchsorted(edges[1:-1], p)
    sizes = np.bincount(group, minlength=bins)
    kept = sizes > 0
    predicted = np.bincount(group, weights=p, minlength=bins)[kept] / sizes[kept]
    observed = np.bincount(group, weights=np.asarray(y, dtype=float), minlength=bins)
    return predicted, observed[kept] / sizes[kept]


def brier(y, probabilities):
    """The mean squared gap between each probability and what happened: 1 for a readmission,
    0 for none."""
    gaps = np.asarray(probabilities, dtype=float) - np.asarray(y, dtype=float)
    return float(np.mean(gaps**2))


def make_boosted():
    """Boosted trees: 50 trees of depth 3 at a learning rate of 0.1, on the counts and age as
    they are and the categories one-hot encoded."""
    encode = ColumnTransformer(
        [
            ("numbers", "passthrough", [*COUNTS, "age"]),
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORIES,
            ),
        ]
    )
    trees = HistGradientBoostingClassifier(
        max_iter=50, max_depth=3, learning_rate=0.1, random_state=SEED
    )
    return make_pipeline(encode, trees)


def make_weighted():
    """The logistic regression with the readmitted stays weighted up, as class_weight="balanced"
    does: together they weigh as much as the stays not readmitted."""
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    return make_pipeline(
        encode, LogisticRegression(max_iter=1000, class_weight="balanced")
    )


def make_chosen():
    """A new, unfitted pipeline of the model to ship."""
    return make_model()


def chosen(table):
    """The model to ship, fitted to every stay in table."""
    return make_chosen().fit(features(table), table["readmitted"])
