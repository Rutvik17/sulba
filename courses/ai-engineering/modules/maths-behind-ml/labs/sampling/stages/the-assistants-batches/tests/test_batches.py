import numpy as np
import pytest

from batches import Batches

N, SIZE = 455, 32


@pytest.fixture(scope="module")
def labels():
    """The records' diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    return table[table[:, 0] == 0, 1]


@pytest.mark.id("tst_9hx31i")
def test_batch_sizes():
    """No batch holds more than size rows"""
    batches = Batches(N, SIZE, 0).epoch(0)
    assert batches
    assert all(len(batch) <= SIZE for batch in batches)


@pytest.mark.id("tst_n6eanf")
def test_reproducible():
    """The same seed and epoch give the same batches"""
    first, again = Batches(N, SIZE, 3).epoch(2), Batches(N, SIZE, 3).epoch(2)
    assert len(first) == len(again)
    assert all(np.array_equal(a, b) for a, b in zip(first, again, strict=True))


@pytest.mark.id("tst_eqpo68")
def test_in_range():
    """Every row number is between 0 and n - 1"""
    rows = np.concatenate(Batches(N, SIZE, 1).epoch(0))
    assert rows.min() >= 0 and rows.max() <= N - 1


@pytest.mark.id("tst_d8vx1i")
def test_average(labels):
    """A batch's average is the mean of its rows"""
    batch = np.arange(SIZE)
    found = Batches(N, SIZE, 0).average(labels, batch)
    assert found == pytest.approx(labels[batch].mean())
