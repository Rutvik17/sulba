import numpy as np
import pytest

from sampling import batch_mean, shuffled_batches


@pytest.fixture(scope="module")
def records():
    """The records' measurements and diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    return table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]


@pytest.mark.id("tst_596yby")
def test_every_record_once(records):
    """Every record once in an epoch, in batches of 32 and one smaller"""
    X, _ = records
    batches = shuffled_batches(len(X), 32, np.random.default_rng(0))
    assert [len(batch) for batch in batches] == [32] * (len(X) // 32) + [len(X) % 32]
    assert np.array_equal(np.sort(np.concatenate(batches)), np.arange(len(X)))


@pytest.mark.id("tst_gw5rqr")
def test_size_that_divides():
    """Equal batches when the size divides the number of records"""
    batches = shuffled_batches(64, 16, np.random.default_rng(1))
    assert [len(batch) for batch in batches] == [16, 16, 16, 16]
    assert np.array_equal(np.sort(np.concatenate(batches)), np.arange(64))


@pytest.mark.id("tst_i6ia4t")
def test_seeds(records):
    """The same seed gives the same batches, and another seed other batches"""
    X, _ = records
    first = np.concatenate(shuffled_batches(len(X), 32, np.random.default_rng(5)))
    again = np.concatenate(shuffled_batches(len(X), 32, np.random.default_rng(5)))
    other = np.concatenate(shuffled_batches(len(X), 32, np.random.default_rng(6)))
    assert np.array_equal(first, again)
    assert not np.array_equal(first, other)


@pytest.mark.id("tst_lbspz5")
def test_batch_mean_by_hand():
    """Batch means of numbers and of rows, worked by hand"""
    assert batch_mean(np.array([1.0, 2.0, 3.0, 4.0, 5.0]), np.array([0, 4])) == 3
    rows = np.array([[1.0, 10.0], [3.0, 20.0], [5.0, 60.0]])
    assert np.asarray(batch_mean(rows, np.array([1, 2]))).tolist() == [4, 40]


@pytest.mark.id("tst_llfvim")
def test_epoch_averages_to_whole(records):
    """An epoch's batch means, weighted by their sizes, average to the records' mean"""
    X, y = records
    batches = shuffled_batches(len(X), 32, np.random.default_rng(2))
    sizes = np.array([len(batch) for batch in batches])
    means = np.array([batch_mean(y, batch) for batch in batches])
    assert np.sum(sizes * means) / np.sum(sizes) == pytest.approx(y.mean(), rel=1e-12)
    worst_area = np.array([batch_mean(X[:, 23], batch) for batch in batches])
    assert np.sum(sizes * worst_area) / np.sum(sizes) == pytest.approx(
        X[:, 23].mean(), rel=1e-12
    )
