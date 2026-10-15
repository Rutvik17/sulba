import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from forest import CATEGORIES, bootstrap, encode, forest_score, grow_forest


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    return [
        (encode(part, categories), (part["subscribed"] == "yes").to_numpy())
        for part in (train, validation)
    ]


@pytest.mark.id("tst_z0syx9")
def test_bootstrap():
    """A bootstrap sample, drawn from the generator"""
    sample = bootstrap(1000, np.random.default_rng(3))
    expected = np.random.default_rng(3).integers(0, 1000, size=1000)
    np.testing.assert_array_equal(sample, expected)


@pytest.mark.id("tst_j32p10")
def test_grow(calls):
    """Each tree grown on its own sample, with its own seed"""
    (X, said_yes), (V, _) = calls
    trees, samples = grow_forest(X, said_yes, 3, np.random.default_rng(5), 10, "sqrt")
    assert len(trees) == len(samples) == 3
    rng = np.random.default_rng(5)
    for tree, sample in zip(trees, samples, strict=True):
        expected = rng.integers(0, len(X), size=len(X))
        seed = int(rng.integers(2**31))
        np.testing.assert_array_equal(sample, expected)
        reference = DecisionTreeClassifier(
            min_samples_leaf=10, max_features="sqrt", random_state=seed
        )
        reference.fit(X[expected], said_yes[expected])
        np.testing.assert_array_equal(tree.predict_proba(V), reference.predict_proba(V))


@pytest.mark.id("tst_6rssv4")
def test_scikit_learn(calls):
    """Scores averaged as scikit-learn's RandomForestClassifier averages its trees'"""
    (X, said_yes), (V, _) = calls
    model = RandomForestClassifier(20, min_samples_leaf=5, random_state=0)
    model.fit(X, said_yes)
    expected = model.predict_proba(V)[:, 1]
    np.testing.assert_allclose(
        forest_score(model.estimators_, V), expected, rtol=0, atol=1e-12
    )


@pytest.mark.id("tst_dylqwc")
def test_one_tree(calls):
    """A forest of one tree, scored as that tree"""
    (X, said_yes), (V, _) = calls
    tree = DecisionTreeClassifier(min_samples_leaf=25).fit(X, said_yes)
    np.testing.assert_array_equal(forest_score([tree], V), tree.predict_proba(V)[:, 1])
