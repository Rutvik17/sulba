import numpy as np
import pandas as pd
import pytest
from sklearn.neighbors import KNeighborsClassifier

from sorter import MEASUREMENTS, nearest, scale, vote

# The neighbours each test bean is sorted by.
K = 15


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    train, test = table[table["set"] == 0], table[table["set"] == 2]
    train_scaled, test_scaled = scale(
        train[MEASUREMENTS].to_numpy(), test[MEASUREMENTS].to_numpy()
    )
    return train_scaled, train["variety"].to_numpy(), test_scaled


def untied(train, test):
    """True for each test bean whose Kth and next nearest training beans aren't as near."""
    model = KNeighborsClassifier(n_neighbors=K + 1, algorithm="brute").fit(
        train, np.zeros(len(train))
    )
    distances, _ = model.kneighbors(test)
    return distances[:, K - 1] < distances[:, K] - 1e-9


@pytest.mark.id("tst_2gc04w")
def test_by_hand():
    """Neighbours and votes worked by hand"""
    train = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 2.0], [3.0, 0.0]])
    varieties = np.array(["SIRA", "CALI", "SIRA", "CALI"])
    neighbours = nearest(train, np.array([[0.9, 0.0], [0.0, 1.8]]), 3)
    assert neighbours.tolist() == [[1, 0, 3], [2, 0, 1]]
    assert vote(varieties, neighbours).tolist() == ["CALI", "SIRA"]


@pytest.mark.id("tst_2v83q6")
def test_tie_in_distance():
    """Training beans as near as each other, the earlier first"""
    train = np.array([[1.0, 1.0], [0.0, 0.0], [0.0, 0.0], [2.0, 2.0]])
    neighbours = nearest(train, np.array([[0.0, 0.0], [1.0, 1.0]]), 3)
    assert neighbours.tolist() == [[1, 2, 0], [0, 1, 2]]


@pytest.mark.id("tst_8hfchi")
def test_scikit_learn_neighbours(beans):
    """scikit-learn's neighbours for the test beans, in its order"""
    train, varieties, test = beans
    model = KNeighborsClassifier(n_neighbors=K, algorithm="brute").fit(train, varieties)
    distances, theirs = model.kneighbors(test)
    # Where no two of a bean's nearest are as near as each other, the order is the same.
    distinct = (np.diff(distances, axis=1) > 1e-9).all(axis=1) & untied(train, test)
    assert distinct.sum() > len(test) // 2
    np.testing.assert_array_equal(nearest(train, test, K)[distinct], theirs[distinct])


@pytest.mark.id("tst_6n6p9b")
def test_tied_vote():
    """A tied vote goes to the nearest of the tied beans"""
    varieties = np.array(["BOMBAY", "SIRA", "CALI", "SIRA", "BOMBAY"])
    assert vote(varieties, np.array([[1, 0]])).tolist() == ["SIRA"]
    assert vote(varieties, np.array([[1, 0, 3, 4]])).tolist() == ["SIRA"]
    assert vote(varieties, np.array([[2, 0, 1]])).tolist() == ["CALI"]
    assert vote(varieties, np.array([[2, 0, 4]])).tolist() == ["BOMBAY"]


@pytest.mark.id("tst_wc3e2p")
def test_scikit_learn_votes(beans):
    """scikit-learn's varieties for the test beans whose vote has one winner"""
    train, varieties, test = beans
    model = KNeighborsClassifier(n_neighbors=K, algorithm="brute").fit(train, varieties)
    shares = np.sort(model.predict_proba(test), axis=1)
    clear = (shares[:, -1] > shares[:, -2]) & untied(train, test)
    mine = vote(varieties, nearest(train, test, K))
    np.testing.assert_array_equal(mine[clear], model.predict(test)[clear])


@pytest.mark.id("tst_3vftkp")
def test_unchanged(beans):
    """The arrays given left as they were"""
    train, varieties, test = beans
    copies = train.copy(), varieties.copy(), test.copy()
    vote(varieties, nearest(train, test[:20], K))
    for given, copy in zip((train, varieties, test), copies):
        np.testing.assert_array_equal(given, copy)
