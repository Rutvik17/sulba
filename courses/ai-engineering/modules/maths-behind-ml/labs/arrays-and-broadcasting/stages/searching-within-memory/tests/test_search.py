import numpy as np
import pytest

from search import Search


@pytest.fixture(scope="module")
def clinic():
    """The records' measurements and diagnoses, and the new samples."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    return table[~new, 2:], table[~new, 1], table[new, 2:]


@pytest.mark.id("tst_x8h9h7")
def test_each_record_finds_itself(clinic):
    """Each record, looked up, is its own nearest record"""
    records, diagnoses, _ = clinic
    near, dist, _ = Search(records.copy(), diagnoses.copy()).find(records.copy(), k=1)
    assert np.array_equal(np.asarray(near)[:, 0], np.arange(len(records)))
    assert np.allclose(np.asarray(dist)[:, 0], 0, rtol=0, atol=1e-12)


@pytest.mark.id("tst_ra4uh8")
def test_shapes(clinic):
    """k records, k distances and one share for each new sample"""
    records, diagnoses, new = clinic
    near, dist, share = Search(records.copy(), diagnoses.copy()).find(new.copy(), k=7)
    assert np.shape(near) == np.shape(dist) == (len(new), 7)
    assert np.shape(share) == (len(new),)


@pytest.mark.id("tst_ahc68a")
def test_arrays_kept(clinic):
    """The arrays it's given stay as they were"""
    records, diagnoses, new = clinic
    given = [records.copy(), diagnoses.copy(), new.copy()]
    Search(given[0], given[1]).find(given[2])
    for kept, original in zip(given, (records, diagnoses, new), strict=True):
        assert np.array_equal(kept, original)


@pytest.mark.id("tst_xspt72")
def test_measurement_with_no_spread(clinic):
    """A measurement that is the same in every record leaves the records found as they were"""
    records, diagnoses, new = clinic
    plain = Search(records.copy(), diagnoses.copy()).find(new.copy())[0]
    records_7, new_7 = (
        np.column_stack([part, np.full(len(part), 7.0)]) for part in (records, new)
    )
    with_it = Search(records_7, diagnoses.copy()).find(new_7)[0]
    assert np.array_equal(with_it, plain)
