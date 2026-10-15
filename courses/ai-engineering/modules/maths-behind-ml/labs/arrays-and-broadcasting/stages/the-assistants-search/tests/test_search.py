import numpy as np
import pytest

from search import search


@pytest.fixture(scope="module")
def records():
    """The records' measurements and diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    in_records = table[:, 0] == 0
    return table[in_records, 2:], table[in_records, 1]


@pytest.mark.id("tst_uzie6a")
def test_each_record_finds_itself(records):
    """Each record, looked up, is its own nearest record"""
    X, diagnoses = records
    near, dist, _ = search(X.copy(), diagnoses.copy(), X.copy(), k=1)
    assert np.array_equal(near[:, 0], np.arange(len(X)))
    assert np.all(dist[:, 0] == 0)


@pytest.mark.id("tst_hobugr")
def test_k_records_each(records):
    """A batch gets k records each, with their distances"""
    X, diagnoses = records
    near, dist, _ = search(X.copy(), diagnoses.copy(), X[:20].copy(), k=5)
    assert near.shape == dist.shape == (20, 5)
    assert np.all((near >= 0) & (near < len(X)))
    assert np.all(dist >= 0)


@pytest.mark.id("tst_rlakym")
def test_shares_from_the_records_found(records):
    """The shares come from the diagnoses of the records found"""
    X, diagnoses = records
    near, _, share = search(X.copy(), diagnoses.copy(), X[:20].copy(), k=5)
    assert np.mean(share) == pytest.approx(np.mean(diagnoses[near]))


@pytest.mark.id("tst_edvyxf")
def test_shares_are_shares(records):
    """Every share is between 0 and 1"""
    X, diagnoses = records
    _, _, share = search(X.copy(), diagnoses.copy(), X[:20].copy(), k=5)
    assert np.all((0 <= share) & (share <= 1))
