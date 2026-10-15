import numpy as np
import pytest

from vectors import Nearest


@pytest.fixture(scope="module")
def clinic():
    """The records and the new samples, standardized with the records' mean and standard
    deviation."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    return (X - mean) / std, (table[new, 2:] - mean) / std


@pytest.mark.id("tst_f6jjcl")
def test_shapes(clinic):
    """k records and k distances for each new sample"""
    records, new = clinic
    near, dist = Nearest(records.copy()).find(new.copy(), k=7)
    assert np.shape(near) == np.shape(dist) == (len(new), 7)


@pytest.mark.id("tst_50shk2")
def test_nearest_first(clinic):
    """Nearest first, at distances of 0 or more"""
    records, new = clinic
    _, dist = Nearest(records.copy()).find(new.copy())
    dist = np.asarray(dist)
    assert np.all(dist >= 0)
    assert np.all(np.diff(dist, axis=1) >= 0)


@pytest.mark.id("tst_n9123a")
def test_arrays_kept(clinic):
    """The arrays it's given stay as they were"""
    records, new = clinic
    given = [records.copy(), new.copy()]
    Nearest(given[0]).find(given[1])
    assert np.array_equal(given[0], records) and np.array_equal(given[1], new)


@pytest.mark.id("tst_a2l46r")
def test_alone_as_in_a_batch(clinic):
    """A sample alone gets what it gets in a batch"""
    records, new = clinic
    search = Nearest(records.copy())
    near, dist = (np.asarray(part) for part in search.find(new.copy()))
    for i in (0, 41, 113):
        alone_near, alone_dist = (
            np.asarray(part) for part in search.find(new[[i]].copy())
        )
        assert np.array_equal(alone_near[0], near[i])
        assert np.allclose(alone_dist[0], dist[i], rtol=1e-12, atol=0)
