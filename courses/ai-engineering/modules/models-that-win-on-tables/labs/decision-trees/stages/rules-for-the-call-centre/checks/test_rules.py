import numpy as np
import pandas as pd
import pytest

from tree import CATEGORIES, NUMBERS, encode, grow, rules, score

# The tree the call centre reads: as deep, and with leaves as large, as the validation
# calls chose.
DEPTH, MIN_LEAF = 6, 25


@pytest.fixture(scope="module")
def bank():
    table = pd.read_csv("data/calls.csv")
    train, validation, test = (table[table["set"] == number] for number in (0, 1, 2))
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    columns = NUMBERS + [(name, c) for name in CATEGORIES for c in categories[name]]
    said_yes = (train["subscribed"] == "yes").to_numpy()
    tree = grow(encode(train, categories), said_yes, DEPTH, MIN_LEAF)
    return train, validation, test, categories, tree, rules(tree, columns)


def meets(calls, conditions):
    """Whether each call meets every condition."""
    met = np.ones(len(calls), dtype=bool)
    for name, (first, second) in conditions.items():
        values = calls[name]
        if first == "is":
            met &= (values == second).to_numpy()
        elif first == "is not":
            met &= ~values.isin(list(second)).to_numpy()
        else:
            met &= ((values > first) & (values <= second)).to_numpy()
    return met


def met(calls, found):
    """For each call, the rules it meets."""
    return np.array([meets(calls, rule["conditions"]) for rule in found]).T


@pytest.mark.id("tst_r4t2r3")
def test_one_rule(bank):
    """Every client meets one rule"""
    _, validation, _, _, _, found = bank
    assert (met(validation, found).sum(axis=1) == 1).all()


@pytest.mark.id("tst_u8fzq8")
def test_counts(bank):
    """Each rule's counts traced to its calls"""
    train, _, _, _, _, found = bank
    said_yes = (train["subscribed"] == "yes").to_numpy()
    for rule, calls in zip(found, met(train, found).T, strict=True):
        assert calls.sum() == rule["calls"]
        assert (calls & said_yes).sum() == rule["yes"]


@pytest.mark.id("tst_ax804c")
def test_tree_share(bank):
    """Each client's rule gives the tree's share"""
    _, validation, _, categories, tree, found = bank
    shares = np.array([rule["yes"] / rule["calls"] for rule in found])
    which = met(validation, found).argmax(axis=1)
    expected = score(tree, encode(validation, categories))
    np.testing.assert_allclose(shares[which], expected, rtol=0, atol=1e-12)


@pytest.mark.id("tst_j1jr71")
def test_new_category(bank):
    """A client in a category the training calls never had"""
    _, _, test, categories, tree, found = bank
    assert "yes" not in categories["default"]
    clients = test[test["default"] == "yes"]
    assert len(clients) > 0
    rows = met(clients, found)
    assert (rows.sum(axis=1) == 1).all()
    shares = np.array([rule["yes"] / rule["calls"] for rule in found])
    expected = score(tree, encode(clients, categories))
    np.testing.assert_allclose(
        shares[rows.argmax(axis=1)], expected, rtol=0, atol=1e-12
    )
