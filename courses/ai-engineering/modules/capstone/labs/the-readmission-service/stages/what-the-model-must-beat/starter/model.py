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
    raise NotImplementedError


def held_out(table):
    """The stays split at random into a part to learn from and 30% held out, each with the
    same share readmitted."""
    raise NotImplementedError


def scores(model, learn, test):
    """The model fitted to learn's stays, and its probability of a readmission for each of
    test's."""
    raise NotImplementedError


def auc(test, probabilities):
    """How well the probabilities rank test's stays: the area under the ROC curve."""
    raise NotImplementedError


def baseline(test):
    """The AUC of ranking test's stays by their inpatient visits in the year before."""
    raise NotImplementedError
