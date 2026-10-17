import math

import numpy as np
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from features import CATEGORIES, COUNTS, features, stays
from model import cross_validated, summary


@pytest.fixture(scope="module")
def table():
    return stays("data/encounters.csv")


@pytest.fixture(scope="module")
def five(table):
    return cross_validated(table)


def reference(table):
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    model = make_pipeline(encode, LogisticRegression(max_iter=1000))
    splitter = StratifiedKFold(5, shuffle=True, random_state=0)
    return cross_val_score(
        model, features(table), table["readmitted"], cv=splitter, scoring="roc_auc"
    )


@pytest.mark.id("tst_xab7v9")
def test_one_per_fold(five):
    """Gives one AUC for each of five folds"""
    assert len(five) == 5


@pytest.mark.id("tst_os446a")
def test_as_scikit_learn(table, five):
    """Gives each fold the AUC scikit-learn's cross_val_score gives it"""
    assert np.allclose(five, reference(table), rtol=0, atol=1e-9)


@pytest.mark.id("tst_usytcr")
def test_other_model_and_folds(table):
    """Cross-validates the model make gives, over the number of folds asked for"""
    # A model that gives every stay the share readmitted ranks none above another.
    constant = cross_validated(table, make=lambda: DummyClassifier(), folds=3)
    assert constant == pytest.approx([0.5, 0.5, 0.5], abs=1e-12)


@pytest.mark.id("tst_vkyf0r")
def test_summary():
    """Gives the mean and its standard error"""
    mean, error = summary([0.6, 0.62, 0.64])
    assert mean == pytest.approx(0.62, abs=1e-12)
    assert error == pytest.approx(0.02 / math.sqrt(3), abs=1e-12)
