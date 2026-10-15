import time
import tracemalloc

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from search import Search

LOOKUPS, RECORDS, BUDGET_MB = 50, 10_000, 32


@pytest.fixture(scope="module")
def clinic():
    """The records' measurements and diagnoses, and the new samples."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    return table[~new, 2:], table[~new, 1], table[new, 2:]


@pytest.fixture(scope="module")
def grown(clinic):
    """Records like the clinic's, each a record with every measurement varied by a few
    percent, and new samples made the same way."""
    records, diagnoses, new = clinic
    rng = np.random.default_rng(0)
    rows = rng.integers(0, len(records), RECORDS)
    many = records[rows] * rng.normal(1, 0.05, (RECORDS, records.shape[1]))
    picked = new[rng.integers(0, len(new), LOOKUPS)]
    return many, diagnoses[rows], picked * rng.normal(1, 0.05, picked.shape)


@pytest.mark.id("tst_ekkp1c")
def test_within_budget(grown, record_property):
    """Within 32 MB"""
    records, diagnoses, new = (part.copy() for part in grown)
    tracemalloc.start()
    try:
        Search(records, diagnoses).find(new)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    record_property("note", f"{peak / 1e6:.0f} MB at its peak")
    assert peak <= BUDGET_MB * 1e6


@pytest.mark.id("tst_jhmzf6")
def test_fast(grown, record_property):
    """Fast on 10,000 records"""
    records, diagnoses, new = (part.copy() for part in grown)
    search = Search(records, diagnoses)
    start = time.perf_counter()
    search.find(new)
    took = time.perf_counter() - start
    record_property("note", f"{took:.2f} seconds")
    assert took < 1


@pytest.mark.id("tst_qz9ggs")
def test_same_as_one_step(clinic):
    """The search's records"""
    records, diagnoses, new = clinic
    near, dist, share = Search(records.copy(), diagnoses.copy()).find(new.copy())
    mean, std = records.mean(axis=0), records.std(axis=0)
    D = cdist((new - mean) / std, (records - mean) / std)
    expected = np.argsort(D, axis=1, kind="stable")[:, :5]
    assert np.array_equal(near, expected)
    assert np.allclose(dist, np.take_along_axis(D, expected, axis=1), rtol=1e-9, atol=0)
    assert np.allclose(share, diagnoses[expected].mean(axis=1), rtol=0, atol=1e-12)


@pytest.mark.id("tst_uken04")
def test_any_batch(grown):
    """Any number of samples"""
    records, diagnoses, new = grown
    search = Search(records.copy(), diagnoses.copy())
    whole = np.asarray(search.find(new.copy())[0])
    for count in (1, 7, 31):
        assert np.array_equal(search.find(new[:count].copy())[0], whole[:count])
    one_by_one = [search.find(new[[i]].copy())[0] for i in range(10)]
    assert np.array_equal(np.concatenate(one_by_one), whole[:10])
