import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

from forest import CATEGORIES, auc_by_count, encode, forest_score, grow_forest


class Fixed:
    """A tree that gives each row a share fixed in advance."""

    def __init__(self, shares):
        self.shares = np.asarray(shares, dtype=float)

    def predict_proba(self, X):
        return np.column_stack([1 - self.shares, self.shares])


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    return [
        (encode(part, categories), (part["subscribed"] == "yes").to_numpy())
        for part in (train, validation)
    ]


@pytest.mark.id("tst_ht5h6f")
def test_by_hand():
    """AUCs of the first one and two trees, worked by hand"""
    said_yes = np.array([False, False, True, True])
    trees = [Fixed([0.1, 0.4, 0.35, 0.8]), Fixed([0.3, 0.0, 0.25, 0.6])]
    aucs = auc_by_count(trees, np.zeros((4, 1)), said_yes)
    # One tree ranks 3 of the 4 yes-no pairs right; the two averaged, all 4.
    np.testing.assert_allclose(aucs, [0.75, 1.0], rtol=0, atol=1e-12)


@pytest.mark.id("tst_uv5zfa")
def test_forest(calls):
    """Each count's AUC, that of the forest of the first trees"""
    (X, said_yes), (V, validation_yes) = calls
    trees, _ = grow_forest(X, said_yes, 8, np.random.default_rng(2), 10, "sqrt")
    aucs = auc_by_count(trees, V, validation_yes)
    assert len(aucs) == len(trees)
    for count in [1, 4, 8]:
        expected = roc_auc_score(validation_yes, forest_score(trees[:count], V))
        assert abs(aucs[count - 1] - expected) < 1e-12


@pytest.mark.id("tst_5bzh3r")
def test_scikit_learn(calls):
    """All the trees' AUC, that of scikit-learn's RandomForestClassifier"""
    (X, said_yes), (V, validation_yes) = calls
    model = RandomForestClassifier(20, min_samples_leaf=10, random_state=0)
    model.fit(X, said_yes)
    expected = roc_auc_score(validation_yes, model.predict_proba(V)[:, 1])
    aucs = auc_by_count(model.estimators_, V, validation_yes)
    assert abs(aucs[-1] - expected) < 1e-12
