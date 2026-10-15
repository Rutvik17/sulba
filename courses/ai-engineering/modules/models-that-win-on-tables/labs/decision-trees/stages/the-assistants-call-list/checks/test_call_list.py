import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from call_list import DEPTHS, call_list, encode, fit, grow, score

# What the bank knows of a client before calling: every column but the call's length and
# its outcome.
UNKNOWN = ["duration", "subscribed"]


@pytest.fixture(scope="module")
def table():
    table = pd.read_csv("data/calls.csv")
    return [table[table["set"] == number] for number in (0, 1, 2)]


@pytest.fixture(scope="module")
def fitted(table):
    train, validation, _ = table
    return fit(train, validation)


def leaves(node):
    if "column" not in node:
        return [node]
    return leaves(node["left"]) + leaves(node["right"])


def cut(tree, depth):
    if depth == 0 or "column" not in tree:
        return {"calls": tree["calls"], "yes": tree["yes"]}
    left, right = cut(tree["left"], depth - 1), cut(tree["right"], depth - 1)
    return {**tree, "left": left, "right": right}


@pytest.mark.id("tst_42gt91")
def test_before_the_call(table, fitted):
    """Tomorrow's clients, not yet called"""
    _, validation, _ = table
    clients = validation.drop(columns=UNKNOWN)
    order, _ = call_list(fitted, clients)
    assert sorted(order) == sorted(clients.index)


@pytest.mark.id("tst_vevp3j")
def test_depth(table, fitted):
    """The depth chosen on the validation calls"""
    train, validation, _ = table
    tree, categories = fitted
    X, said_yes = encode(train, categories), (train["subscribed"] == "yes").to_numpy()
    V = encode(validation, categories)
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    deep = grow(X, said_yes, max(DEPTHS))
    aucs = [roc_auc_score(validation_yes, score(cut(deep, d), V)) for d in DEPTHS]
    assert tree == cut(deep, DEPTHS[int(np.argmax(aucs))])


@pytest.mark.id("tst_78lmv3")
def test_min_leaf(table, fitted):
    """At least 25 training calls in every leaf"""
    train, _, _ = table
    _, categories = fitted
    X, said_yes = encode(train, categories), (train["subscribed"] == "yes").to_numpy()
    assert min(leaf["calls"] for leaf in leaves(grow(X, said_yes, 6, 25))) >= 25


@pytest.mark.id("tst_3uyna1")
def test_new_category(table, fitted):
    """A client in a category the training calls never had"""
    train, _, test = table
    assert not (train["default"] == "yes").any()
    clients = test.drop(columns=["subscribed"])
    order, _ = call_list(fitted, clients)
    assert sorted(order) == sorted(clients.index)
