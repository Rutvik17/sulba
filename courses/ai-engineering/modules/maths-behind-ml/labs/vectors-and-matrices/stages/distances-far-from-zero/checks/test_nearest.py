import tracemalloc

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from vectors import Nearest

K, SHIFT = 5, 100_000_000
LOOKUPS, RECORDS, BUDGET_MB = 50, 10_000, 32


@pytest.fixture(scope="module")
def clinic():
    """The records and the new samples, standardized with the records' mean and standard
    deviation, and the records as measured."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    return (X - mean) / std, (table[new, 2:] - mean) / std, X


def same_as_cdist(records, new):
    """Whether find gives the k records nearest each new sample, nearest first, at the
    distances SciPy's cdist gives."""
    near, dist = Nearest(records.copy()).find(new.copy(), k=K)
    D = cdist(new, records)
    expected = np.argsort(D, axis=1, kind="stable")[:, :K]
    return np.array_equal(near, expected) and np.allclose(
        dist, np.take_along_axis(D, expected, axis=1), rtol=1e-9, atol=0
    )


@pytest.mark.id("tst_ugbjqx")
def test_same_as_cdist(clinic):
    """The search's records"""
    records, new, _ = clinic
    assert same_as_cdist(records, new)


@pytest.mark.id("tst_ucsu0s")
def test_far_from_zero(clinic):
    """Far from 0"""
    records, new, _ = clinic
    assert same_as_cdist(records + SHIFT, new + SHIFT)


@pytest.mark.id("tst_4x6s5j")
def test_records_find_themselves(clinic):
    """Samples already in the records"""
    records, _, measured = clinic
    for table in (records, measured):
        near, dist = Nearest(table.copy()).find(table.copy(), k=K)
        assert np.array_equal(np.asarray(near)[:, 0], np.arange(len(table)))
        assert np.all(np.asarray(dist)[:, 0] == 0)


@pytest.fixture(scope="module")
def grown(clinic):
    """Records like the clinic's, as measured, each a record with every measurement varied
    by a few percent, and new samples made the same way."""
    _, _, measured = clinic
    rng = np.random.default_rng(0)
    many = measured[rng.integers(0, len(measured), RECORDS)]
    many = many * rng.normal(1, 0.05, many.shape)
    picked = measured[rng.integers(0, len(measured), LOOKUPS)]
    return many, picked * rng.normal(1, 0.05, picked.shape)


@pytest.mark.id("tst_6gd55k")
def test_within_budget(grown, record_property):
    """Within 32 MB"""
    records, new = (part.copy() for part in grown)
    tracemalloc.start()
    try:
        Nearest(records).find(new)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    record_property("note", f"{peak / 1e6:.0f} MB at its peak")
    assert peak <= BUDGET_MB * 1e6
