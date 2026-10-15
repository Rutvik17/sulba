import numpy as np
import pytest
from sklearn.neighbors import NearestNeighbors

from similar import distances, malignant_share, nearest, standardize


@pytest.fixture(scope="module")
def standardized():
    """The records, standardized, with their diagnoses, and the new samples on their scale."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    records, samples = table[~new, 2:], table[new, 2:]
    mean, std = records.mean(axis=0), records.std(axis=0)
    return (
        standardize(records, mean, std),
        table[~new, 1],
        standardize(samples, mean, std),
    )


@pytest.mark.id("tst_kgyz77")
def test_small_case():
    """The k smallest in each row, smallest first"""
    D = np.array([[3.0, 1.0, 2.0], [0.5, 0.2, 0.9]])
    assert np.asarray(nearest(D, 2)).tolist() == [[1, 2], [1, 0]]


@pytest.mark.id("tst_007jb6")
def test_ties_in_column_order():
    """Equal distances come in column order"""
    D = np.array([[1.0, 0.0, 1.0, 0.0, 1.0]])
    assert np.asarray(nearest(D, 5)).tolist() == [[1, 3, 0, 2, 4]]


@pytest.mark.id("tst_gdmtpa")
def test_same_as_scikit_learn(standardized):
    """The same records as scikit-learn's NearestNeighbors finds, for every k"""
    records, _, samples = standardized
    D = distances(samples, records)
    for k in (1, 5, 25):
        found = nearest(D.copy(), k)
        neighbours = NearestNeighbors(n_neighbors=k, algorithm="brute").fit(records)
        expected = neighbours.kneighbors(samples, return_distance=False)
        assert np.array_equal(found, expected)


@pytest.mark.id("tst_e0mddh")
def test_each_record_finds_itself(standardized):
    """Each record is its own nearest record"""
    records, _, _ = standardized
    found = nearest(distances(records, records), 1)
    assert np.array_equal(np.asarray(found)[:, 0], np.arange(len(records)))


@pytest.mark.id("tst_qfw40p")
def test_small_shares():
    """The share of malignant records in each row, worked by hand"""
    near = np.array([[0, 1], [2, 2], [1, 3]])
    diagnoses = np.array([1.0, 0.0, 1.0, 0.0])
    assert np.asarray(malignant_share(near, diagnoses)).tolist() == [0.5, 1.0, 0.0]


@pytest.mark.id("tst_j1vydf")
def test_one_share_per_sample(standardized):
    """One share for each new sample, from the records found for it"""
    records, diagnoses, samples = standardized
    near = np.argsort(distances(samples, records), axis=1, kind="stable")[:, :5]
    share = malignant_share(near, diagnoses.copy())
    assert np.shape(share) == (len(samples),)
    assert np.allclose(
        share, [diagnoses[row].mean() for row in near], rtol=0, atol=1e-12
    )
