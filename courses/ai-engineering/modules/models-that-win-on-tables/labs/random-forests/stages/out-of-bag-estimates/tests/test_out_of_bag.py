import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from forest import CATEGORIES, encode, grow_forest, out_of_bag


class Fixed:
    """A tree that gives each row a share fixed in advance."""

    def __init__(self, shares):
        self.shares = np.asarray(shares, dtype=float)

    def predict_proba(self, X):
        rows = X[:, 0].astype(int)
        shares = self.shares[rows]
        return np.column_stack([1 - shares, shares])


@pytest.mark.id("tst_q3ukle")
def test_by_hand():
    """Each row scored by the trees that left it out, NaN where none did"""
    X = np.arange(4.0)[:, None]
    trees = [Fixed([0.1, 0.2, 0.3, 0.4]), Fixed([0.5, 0.6, 0.7, 0.8])]
    samples = [np.array([0, 1, 2, 2]), np.array([0, 1, 3, 3])]
    found = out_of_bag(trees, samples, X)
    np.testing.assert_allclose(found, [np.nan, np.nan, 0.7, 0.4], rtol=0, atol=1e-12)


@pytest.mark.id("tst_v8e29u")
def test_scikit_learn():
    """Out-of-bag shares matched to scikit-learn's RandomForestClassifier"""
    table = pd.read_csv("data/calls.csv")
    train = table[table["set"] == 0]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, said_yes = encode(train, categories), (train["subscribed"] == "yes").to_numpy()
    model = RandomForestClassifier(
        30, min_samples_leaf=5, oob_score=True, random_state=0
    )
    model.fit(X, said_yes)
    found = out_of_bag(model.estimators_, model.estimators_samples_, X)
    expected = model.oob_decision_function_[:, 1]
    np.testing.assert_allclose(found, expected, rtol=0, atol=1e-12)


@pytest.mark.id("tst_krra8h")
def test_one_tree():
    """A forest of one tree: the rows it left out scored by it, the rest NaN"""
    table = pd.read_csv("data/calls.csv")
    train = table[table["set"] == 0]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, said_yes = encode(train, categories), (train["subscribed"] == "yes").to_numpy()
    trees, samples = grow_forest(X, said_yes, 1, np.random.default_rng(4), 10, "sqrt")
    found = out_of_bag(trees, samples, X)
    left_out = np.ones(len(X), dtype=bool)
    left_out[samples[0]] = False
    assert np.isnan(found[~left_out]).all()
    expected = trees[0].predict_proba(X[left_out])[:, 1]
    np.testing.assert_allclose(found[left_out], expected, rtol=0, atol=1e-12)
