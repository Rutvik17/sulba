import numpy as np
import pandas as pd
import pytest

from sorter import MEASUREMENTS, choose_k, sort_beans


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    parts = [table[table["set"] == number] for number in (0, 1, 2)]
    return [
        (part[MEASUREMENTS].to_numpy(), part["variety"].to_numpy()) for part in parts
    ]


def named_here(train, varieties, batch, ks):
    """Each bean of batch named for each k of ks the way the brief describes, worked out
    here."""
    mean, sd = train.mean(axis=0), train.std(axis=0)
    train, batch = (train - mean) / sd, (batch - mean) / sd
    orders = [
        np.argsort(((train - bean) ** 2).sum(axis=1), kind="stable") for bean in batch
    ]
    chosen = {k: [] for k in ks}
    for order in orders:
        for k in ks:
            named = list(varieties[order[:k]])
            most = max(named.count(name) for name in named)
            chosen[k].append(next(name for name in named if named.count(name) == most))
    return {k: np.array(names) for k, names in chosen.items()}


@pytest.mark.id("tst_t5h123")
def test_sort_beans(beans):
    """The test beans named by their nearest training beans"""
    (train, varieties), _, (test, _) = beans
    test = test[:200]
    expected = named_here(train, varieties, test, [1, 4, 15])
    for k, names in expected.items():
        np.testing.assert_array_equal(sort_beans(train, varieties, test, k), names)


@pytest.mark.id("tst_iinqd1")
def test_shares(beans):
    """The share of the validation beans each k names right"""
    (train, varieties), (validation, truth), _ = beans
    ks = [1, 2, 15]
    shares, _ = choose_k(train, varieties, validation, truth, ks)
    named = named_here(train, varieties, validation, ks)
    expected = [(named[k] == truth).mean() for k in ks]
    np.testing.assert_allclose(shares, expected, rtol=0, atol=1e-12)


@pytest.mark.id("tst_wwqe0v")
def test_smallest_of_the_tied():
    """The smallest of the k that name the most right"""
    train = np.array([[0.0], [1.0], [10.0], [11.0]])
    varieties = np.array(["CALI", "CALI", "SIRA", "SIRA"])
    validation, truth = np.array([[0.5], [10.5]]), np.array(["CALI", "SIRA"])
    shares, best = choose_k(train, varieties, validation, truth, [3, 1, 2])
    assert list(shares) == [1.0, 1.0, 1.0]
    assert best == 1


@pytest.mark.id("tst_dgczby")
def test_training_beans_themselves(beans):
    """Training beans named right by themselves, with k = 1"""
    (train, varieties), _, _ = beans
    shares, best = choose_k(train, varieties, train[:300], varieties[:300], [1, 5, 15])
    assert shares[0] == 1.0
    assert best == 1


@pytest.mark.id("tst_1egmbu")
def test_unchanged(beans):
    """The arrays given left as they were"""
    (train, varieties), (validation, truth), _ = beans
    given = [train, varieties, validation, truth]
    copies = [array.copy() for array in given]
    choose_k(train, varieties, validation[:50], truth[:50], [1, 3])
    sort_beans(train, varieties, validation[:20], 3)
    for array, copy in zip(given, copies):
        np.testing.assert_array_equal(array, copy)
