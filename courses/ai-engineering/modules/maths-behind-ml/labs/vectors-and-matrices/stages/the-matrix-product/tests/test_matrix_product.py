import numpy as np
import pytest
from scipy.spatial.distance import cdist

from vectors import fast_distances, pairwise_dots


@pytest.fixture(scope="module")
def clinic():
    """The new samples and the records, standardized with the records' mean and standard
    deviation."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    return (table[new, 2:] - mean) / std, (X - mean) / std


@pytest.mark.id("tst_suodg8")
def test_small_case():
    """Two rows against three, worked by hand"""
    A = np.array([[1.0, 1.0], [2.0, 3.0]])
    B = np.array([[1.0, 2.0], [1.0, 0.0], [0.0, 0.0]])
    assert np.asarray(pairwise_dots(A, B)).tolist() == [[3, 1, 0], [8, 2, 0]]


@pytest.mark.id("tst_1cidy9")
def test_same_as_numpy(clinic):
    """Each entry is the dot product of a new sample with a record"""
    new, records = clinic
    dots = np.asarray(pairwise_dots(new.copy(), records.copy()))
    assert dots.shape == (len(new), len(records))
    for i, j in [(0, 0), (3, 200), (113, 454), (57, 17)]:
        assert dots[i, j] == pytest.approx(
            np.dot(new[i], records[j]), rel=1e-12, abs=1e-12
        )


@pytest.mark.id("tst_stk5h7")
def test_same_as_scipy(clinic):
    """The same distances as SciPy's cdist, for every new sample and record"""
    new, records = clinic
    found = np.asarray(fast_distances(new.copy(), records.copy()))
    assert found.shape == (len(new), len(records))
    assert np.allclose(found, cdist(new, records), rtol=1e-9, atol=0)


@pytest.mark.id("tst_zfcmkw")
def test_one_row(clinic):
    """One sample against every record, and every sample against one record"""
    new, records = clinic
    D = cdist(new, records)
    alone = np.asarray(fast_distances(new[[5]], records))
    assert alone.shape == (1, len(records))
    assert np.allclose(alone[0], D[5], rtol=1e-9, atol=0)
    one = np.asarray(fast_distances(new, records[[9]]))
    assert one.shape == (len(new), 1)
    assert np.allclose(one[:, 0], D[:, 9], rtol=1e-9, atol=0)


@pytest.mark.id("tst_2b7nqi")
def test_never_below_zero(clinic):
    """Never nan, even where rounding takes a squared distance below 0"""
    _, records = clinic
    # Worked out from dot products, this squared distance can round to -4, not 0.5625.
    A, B = np.array([[100_000_000.75]]), np.array([[100_000_001.5]])
    far = np.asarray(fast_distances(A, B))
    assert far.shape == (1, 1)
    assert far[0, 0] >= 0
    own = np.asarray(fast_distances(records[:50], records[:50]))
    assert not np.any(np.isnan(own))
    assert np.all(own >= 0)
