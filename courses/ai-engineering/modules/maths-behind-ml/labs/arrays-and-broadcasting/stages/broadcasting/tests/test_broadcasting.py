import numpy as np
import pytest
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler

from similar import distances, standardize


@pytest.fixture(scope="module")
def samples():
    """The records' measurements and the new samples', from the lab's data."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    return table[~new, 2:], table[new, 2:]


@pytest.mark.id("tst_ivo38m")
def test_same_as_scikit_learn(samples):
    """New samples standardized as StandardScaler's transform does it"""
    records, new = samples
    scaler = StandardScaler().fit(records)
    found = standardize(new.copy(), scaler.mean_.copy(), scaler.scale_.copy())
    assert np.shape(found) == new.shape
    assert np.allclose(found, scaler.transform(new), rtol=0, atol=1e-12)


@pytest.mark.id("tst_z5gu27")
def test_no_spread():
    """A column with no spread is divided by 1"""
    X = np.array([[1.0, 5.0], [3.0, 5.0]])
    found = standardize(X, np.array([2.0, 5.0]), np.array([1.0, 0.0]))
    assert np.asarray(found).tolist() == [[-1, 0], [1, 0]]


@pytest.mark.id("tst_3za5fs")
def test_inputs_kept(samples):
    """The arrays it's given stay as they were"""
    records, new = samples
    mean, std = records.mean(axis=0), records.std(axis=0)
    given = [array.copy() for array in (new, mean, std, records)]
    standardize(given[0], given[1], given[2])
    distances(given[0], given[3])
    for kept, original in zip(given, (new, mean, std, records), strict=True):
        assert np.array_equal(kept, original)


@pytest.mark.id("tst_514m3m")
def test_small_case():
    """Two points against three, worked by hand"""
    A = np.array([[0.0, 0.0], [3.0, 4.0]])
    B = np.array([[0.0, 0.0], [3.0, 0.0], [6.0, 8.0]])
    assert np.asarray(distances(A, B)).tolist() == [[0, 3, 10], [5, 4, 5]]


@pytest.mark.id("tst_f20xf6")
def test_same_as_scipy(samples):
    """Every distance from a new sample to a record, as SciPy's cdist gives it"""
    records, new = samples
    found = distances(new, records)
    assert np.shape(found) == (len(new), len(records))
    assert np.allclose(found, cdist(new, records), rtol=1e-12, atol=0)


@pytest.mark.id("tst_p8kxo4")
def test_one_row(samples):
    """One row against many, and many against one"""
    records, new = samples
    assert np.shape(distances(new[:1], records)) == (1, len(records))
    assert np.shape(distances(new, records[:1])) == (len(new), 1)
    assert np.allclose(
        distances(new[:1], records)[0], cdist(new[:1], records)[0], rtol=1e-12
    )
