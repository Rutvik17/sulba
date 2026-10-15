import numpy as np
import pandas as pd
import pytest

from report import CATEGORIES, NUMBERS, encode, grow, importance, score


class Fixed:
    """A tree that gives each row the share in its first column."""

    def predict_proba(self, X):
        return np.column_stack([1 - X[:, 0], X[:, 0]])


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/calls.csv")


@pytest.mark.id("tst_tiatol")
def test_encode(table):
    """One column of 0 and 1 for each category, a 1 in each category column"""
    categories = {name: sorted(table[name].unique()) for name in CATEGORIES}
    ones = encode(table.head(20), categories)[:, len(NUMBERS) :]
    assert set(np.unique(ones)) <= {0.0, 1.0}
    assert (ones.sum(axis=1) == len(CATEGORIES)).all()


@pytest.mark.id("tst_fsh2rm")
def test_grow(table):
    """A tree for each sample, each sample as long as the calls"""
    train = table[table["set"] == 0].head(300)
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, said_yes = encode(train, categories), (train["subscribed"] == "yes").to_numpy()
    trees, samples = grow(X, said_yes, 4, np.random.default_rng(0))
    assert len(trees) == len(samples) == 4
    assert all(len(sample) == len(X) for sample in samples)


@pytest.mark.id("tst_wtkhij")
def test_score():
    """The trees' shares averaged"""
    X = np.array([[0.2], [0.6]])
    np.testing.assert_allclose(score([Fixed(), Fixed()], X), [0.2, 0.6])


@pytest.mark.id("tst_21pnuz")
def test_importance(table):
    """A fall in AUC for every column"""
    validation = table[table["set"] == 1]
    categories = {name: sorted(table[name].unique()) for name in CATEGORIES}
    falls = importance([Fixed()], validation, categories, np.random.default_rng(0))
    assert sorted(falls) == sorted(NUMBERS + CATEGORIES)
