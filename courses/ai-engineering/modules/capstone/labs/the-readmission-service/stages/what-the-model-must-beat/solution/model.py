"""The readmission model: its pipeline, and the scores it's judged by."""

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
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
