import numpy as np
import pytest

from search import search


@pytest.fixture(scope="module")
def clinic():
    """The records' measurements and diagnoses, and the new samples."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    return table[~new, 2:], table[~new, 1], table[new, 2:]


def found(records, diagnoses, new, k=5):
    """The search, given copies, so that no call sees what another changed."""
    return search(records.copy(), diagnoses.copy(), new.copy(), k)


@pytest.mark.id("tst_n7l9iy")
def test_alone_as_in_a_batch(clinic):
    """A new sample gets the same records alone as in a batch"""
    records, diagnoses, new = clinic
    batch, _, _ = found(records, diagnoses, new)
    for i in range(0, len(new), 10):
        alone, _, _ = found(records, diagnoses, new[i : i + 1])
        assert sorted(np.asarray(alone)[0].tolist()) == sorted(
            np.asarray(batch)[i].tolist()
        )


@pytest.mark.id("tst_aevk2n")
def test_measurement_with_no_spread(clinic):
    """A measurement that is the same in every record leaves the records found as they were"""
    records, diagnoses, new = clinic
    plain, _, _ = found(records, diagnoses, new)
    records_7, new_7 = (
        np.column_stack([part, np.full(len(part), 7.0)]) for part in (records, new)
    )
    with_it, _, _ = found(records_7, diagnoses, new_7)
    assert np.array_equal(np.sort(with_it, axis=1), np.sort(plain, axis=1))


@pytest.mark.id("tst_3ctqre")
def test_arrays_kept(clinic):
    """The records, diagnoses and samples it's given stay as they were"""
    records, diagnoses, new = clinic
    given = [records.copy(), diagnoses.copy(), new.copy()]
    search(*given, 5)
    for kept, original in zip(given, (records, diagnoses, new), strict=True):
        assert np.array_equal(kept, original)


@pytest.mark.id("tst_deuu63")
def test_share_for_each_sample(clinic):
    """Each new sample gets the share of malignant records among its own records"""
    records, diagnoses, new = clinic
    near, _, share = found(records, diagnoses, new)
    assert np.shape(share) == (len(new),)
    assert np.allclose(share, diagnoses[near].mean(axis=1), rtol=0, atol=1e-12)
