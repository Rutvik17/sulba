import numpy as np
import pandas as pd
import pytest

from call_list import CATEGORIES, NUMBERS, best_split, call_list, encode, grow


@pytest.fixture(scope="module")
def table():
    return pd.read_csv("data/calls.csv")


@pytest.mark.id("tst_mxjr60")
def test_encode(table):
    """One column of 0 and 1 for each category, a 1 in each category column"""
    categories = {name: sorted(table[name].unique()) for name in CATEGORIES}
    ones = encode(table.head(20), categories)[:, len(NUMBERS) :]
    assert set(np.unique(ones)) <= {0.0, 1.0}
    assert (ones.sum(axis=1) == len(CATEGORIES)).all()


@pytest.mark.id("tst_38ivwf")
def test_best_split():
    """A split worked by hand"""
    column = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    said_yes = np.array([False, False, True, False, True, True])
    threshold, impurity = best_split(column, said_yes, 1)
    assert threshold == 2.5
    assert abs(impurity - 0.25) < 1e-12


@pytest.mark.id("tst_uhellb")
def test_grow():
    """Calls one split separates, in two leaves"""
    X = np.array([[1.0], [2.0], [3.0], [4.0]])
    tree = grow(X, np.array([False, False, True, True]), 3, 1)
    assert tree["threshold"] == 2.5
    assert tree["left"] == {"calls": 2, "yes": 0}
    assert tree["right"] == {"calls": 2, "yes": 2}


@pytest.mark.id("tst_ylu8ji")
def test_call_list(table):
    """The clients over 40 called first"""
    categories = {name: sorted(table[name].unique()) for name in CATEGORIES}
    # A tree that splits the first number column, age.
    tree = {
        "calls": 10,
        "yes": 3,
        "column": 0,
        "threshold": 40.5,
        "left": {"calls": 6, "yes": 1},
        "right": {"calls": 4, "yes": 2},
    }
    clients = table.head(20)
    order, shares = call_list((tree, categories), clients)
    older = clients.index[clients["age"] > 40.5]
    assert sorted(order) == sorted(clients.index)
    assert set(order[: len(older)]) == set(older)
    assert (np.diff(shares) <= 0).all()
