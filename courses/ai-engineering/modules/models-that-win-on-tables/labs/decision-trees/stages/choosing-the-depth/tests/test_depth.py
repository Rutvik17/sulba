import copy

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeClassifier

from tree import CATEGORIES, choose_depth, encode, grow, prune

DEPTHS = [1, 2, 3, 4, 5, 6, 7, 8]


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    return [
        (encode(part, categories), (part["subscribed"] == "yes").to_numpy())
        for part in (train, validation)
    ]


@pytest.mark.id("tst_ep11xh")
def test_by_hand():
    """A tree cut by hand, and the tree it was cut from left as it was"""
    tree = {
        "calls": 6,
        "yes": 2,
        "column": 0,
        "threshold": 3.5,
        "left": {"calls": 3, "yes": 0},
        "right": {
            "calls": 3,
            "yes": 2,
            "column": 1,
            "threshold": 0.5,
            "left": {"calls": 1, "yes": 0},
            "right": {"calls": 2, "yes": 2},
        },
    }
    kept = copy.deepcopy(tree)
    assert prune(tree, 0) == {"calls": 6, "yes": 2}
    assert prune(tree, 1) == {
        "calls": 6,
        "yes": 2,
        "column": 0,
        "threshold": 3.5,
        "left": {"calls": 3, "yes": 0},
        "right": {"calls": 3, "yes": 2},
    }
    assert prune(tree, 5) == kept
    assert tree == kept


@pytest.mark.id("tst_evc5r8")
def test_cut(calls):
    """A tree cut at a depth, the tree grown to that depth"""
    (X, said_yes), _ = calls
    tree = grow(X, said_yes, 6, 25)
    for depth in [1, 3, 5]:
        assert prune(tree, depth) == grow(X, said_yes, depth, 25)


@pytest.mark.id("tst_zuenyk")
def test_scikit_learn(calls):
    """Training and validation AUCs, matched to scikit-learn's trees"""
    (X, said_yes), (V, validation_yes) = calls
    trained, validated, best = choose_depth(X, said_yes, V, validation_yes, DEPTHS, 50)
    assert len(trained) == len(validated) == len(DEPTHS)
    expected = []
    for i, depth in enumerate(DEPTHS):
        model = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=50)
        model.fit(X, said_yes)
        train_auc = roc_auc_score(said_yes, model.predict_proba(X)[:, 1])
        expected.append(roc_auc_score(validation_yes, model.predict_proba(V)[:, 1]))
        assert abs(trained[i] - train_auc) < 1e-12
        assert abs(validated[i] - expected[i]) < 1e-12
    assert best == DEPTHS[int(np.argmax(expected))]


@pytest.mark.id("tst_actfx6")
def test_smallest_best():
    """The smallest of the depths tied for the best validation AUC"""
    # One split separates these calls, so every depth gives the same tree.
    X = np.array([[1.0], [2.0], [3.0], [4.0]])
    said_yes = np.array([False, False, True, True])
    trained, validated, best = choose_depth(X, said_yes, X, said_yes, [1, 2, 3], 1)
    assert list(trained) == list(validated) == [1.0, 1.0, 1.0]
    assert best == 1
