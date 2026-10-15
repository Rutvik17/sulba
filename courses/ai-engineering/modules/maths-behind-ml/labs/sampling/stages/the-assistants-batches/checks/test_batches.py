import numpy as np
import pytest

from batches import Batches

N, SIZE = 455, 32


@pytest.fixture(scope="module")
def labels():
    """The records' diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    return table[table[:, 0] == 0, 1]


@pytest.mark.id("tst_ku6ili")
def test_new_order():
    """Each epoch in a new order, the same each time it's asked for"""
    batches = Batches(N, SIZE, 0)
    first, second = np.concatenate(batches.epoch(0)), np.concatenate(batches.epoch(1))
    assert not np.array_equal(first, second)
    assert np.array_equal(np.concatenate(batches.epoch(1)), second)


@pytest.mark.id("tst_2wfkai")
def test_no_repeats():
    """No record twice in an epoch"""
    batches = Batches(N, SIZE, 0)
    for number in range(5):
        rows = np.concatenate(batches.epoch(number))
        assert len(np.unique(rows)) == len(rows)


@pytest.mark.id("tst_c5fdqy")
def test_short_batch_kept():
    """Every epoch's batches hold all the records, the last batch shorter"""
    for number in range(5):
        sizes = [len(batch) for batch in Batches(N, SIZE, 0).epoch(number)]
        assert sizes == [SIZE] * (N // SIZE) + [N % SIZE]


@pytest.mark.id("tst_nqoqhk")
def test_short_average(labels):
    """A short batch's average is the mean of its rows"""
    batch = np.arange(N % SIZE)
    found = Batches(N, SIZE, 0).average(labels, batch)
    assert found == pytest.approx(labels[batch].mean())
