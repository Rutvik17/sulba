import numpy as np
import pandas as pd
import pytest
from sklearn.tree import DecisionTreeClassifier

from tree import CATEGORIES, encode, grow, score


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    return [
        (encode(part, categories), (part["subscribed"] == "yes").to_numpy())
        for part in (train, validation)
    ]


def leaves(node):
    if "column" not in node:
        return [node]
    return leaves(node["left"]) + leaves(node["right"])


@pytest.mark.id("tst_tmst2s")
def test_encode():
    """Categories as columns of 0 and 1, and a category not listed in none of them"""
    numbers = {
        "age": [30, 61],
        "campaign": [1, 3],
        "pdays": [999, 6],
        "previous": [0, 1],
    }
    calls = pd.DataFrame({**numbers, **{name: ["a", "b"] for name in CATEGORIES}})
    calls.loc[1, "job"] = "pilot"
    X = encode(calls, {name: ["a", "b"] for name in CATEGORIES})
    first = [30, 1, 999, 0] + [1, 0] * len(CATEGORIES)
    second = [61, 3, 6, 1] + [0, 0] + [0, 1] * (len(CATEGORIES) - 1)
    np.testing.assert_array_equal(X, [first, second])


@pytest.mark.id("tst_d6r1xx")
def test_by_hand():
    """A tree worked by hand"""
    X = np.array(
        [[1.0, 0.0], [2.0, 1.0], [3.0, 0.0], [4.0, 1.0], [5.0, 1.0], [6.0, 1.0]]
    )
    said_yes = np.array([False, False, False, True, True, False])
    assert grow(X, said_yes, 2, 1) == {
        "calls": 6,
        "yes": 2,
        "column": 0,
        "threshold": 3.5,
        "left": {"calls": 3, "yes": 0},
        "right": {
            "calls": 3,
            "yes": 2,
            "column": 0,
            "threshold": 5.5,
            "left": {"calls": 2, "yes": 2},
            "right": {"calls": 1, "yes": 0},
        },
    }


@pytest.mark.id("tst_6g825e")
def test_leaves():
    """A leaf when the depth runs out, every call agrees, or no split keeps min_leaf a side"""
    X = np.array([[1.0], [2.0], [3.0], [4.0]])
    mixed = np.array([True, False, True, False])
    assert grow(X, mixed, 0, 1) == {"calls": 4, "yes": 2}
    assert grow(X, np.array([True, True, True, True]), 3, 1) == {"calls": 4, "yes": 4}
    assert grow(X, mixed, 3, 3) == {"calls": 4, "yes": 2}


@pytest.mark.id("tst_5xgx3e")
def test_ties():
    """Of columns that split alike, the first"""
    X = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0], [4.0, 4.0]])
    assert grow(X, np.array([False, False, True, True]), 1, 1)["column"] == 0


@pytest.mark.id("tst_lnkvr1")
def test_scikit_learn(calls):
    """The validation calls' scores, matched to scikit-learn's DecisionTreeClassifier"""
    (X, said_yes), (V, _) = calls
    for depth, min_leaf in [(6, 25), (8, 100)]:
        model = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=min_leaf)
        expected = model.fit(X, said_yes).predict_proba(V)[:, 1]
        found = score(grow(X, said_yes, depth, min_leaf), V)
        np.testing.assert_allclose(found, expected, rtol=0, atol=1e-12)


@pytest.mark.id("tst_krlfb1")
def test_min_leaf(calls):
    """Every training call in one leaf, and min_leaf in each"""
    (X, said_yes), _ = calls
    counts = [leaf["calls"] for leaf in leaves(grow(X, said_yes, 10, 50))]
    assert min(counts) >= 50
    assert sum(counts) == len(X)
