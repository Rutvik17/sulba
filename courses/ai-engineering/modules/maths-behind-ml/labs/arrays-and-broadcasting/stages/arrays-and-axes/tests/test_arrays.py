import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler

from similar import column_stats, split


@pytest.fixture(scope="module")
def table():
    """The lab's data: a row per sample."""
    return np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)


@pytest.mark.id("tst_1vet3r")
def test_parts(table):
    """The records and the new samples, each with its diagnoses"""
    records, diagnoses, new, new_diagnoses = split(table.copy())
    assert records.shape == (455, 30)
    assert diagnoses.shape == (455,)
    assert new.shape == (114, 30)
    assert new_diagnoses.shape == (114,)
    assert (diagnoses.sum(), new_diagnoses.sum()) == (170, 42)


@pytest.mark.id("tst_fv82nr")
def test_rows_in_order(table):
    """Each part keeps its rows in the table's order"""
    records, diagnoses, new, new_diagnoses = split(table.copy())
    first_new = int(np.flatnonzero(table[:, 0] == 1)[0])
    last_record = int(np.flatnonzero(table[:, 0] == 0)[-1])
    assert np.array_equal(records[0], table[0, 2:])
    assert np.array_equal(records[-1], table[last_record, 2:])
    assert np.array_equal(new[0], table[first_new, 2:])
    assert (diagnoses[0], new_diagnoses[0]) == (table[0, 1], table[first_new, 1])


@pytest.mark.id("tst_29931l")
def test_small_case():
    """Two rows, worked by hand: each column's mean and standard deviation"""
    mean, std = column_stats(np.array([[1.0, 2.0, 3.0], [3.0, 6.0, 3.0]]))
    assert np.asarray(mean).tolist() == [2, 4, 3]
    assert np.asarray(std).tolist() == [1, 2, 0]


@pytest.mark.id("tst_f10693")
def test_same_as_scikit_learn(table):
    """The same means and standard deviations as StandardScaler's"""
    records = split(table.copy())[0]
    mean, std = column_stats(records.copy())
    scaler = StandardScaler().fit(records)
    assert np.shape(mean) == np.shape(std) == (30,)
    assert np.allclose(mean, scaler.mean_, rtol=1e-12, atol=0)
    assert np.allclose(std, scaler.scale_, rtol=1e-12, atol=0)
