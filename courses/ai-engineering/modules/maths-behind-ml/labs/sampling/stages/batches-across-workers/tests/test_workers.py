import numpy as np
import pytest

from sampling import worker_batches

N, SIZE = 455, 32


def records(n, size, workers, rank, epoch, seed):
    """The row numbers of a worker's batches, in order."""
    return np.concatenate(worker_batches(n, size, workers, rank, epoch, seed))


@pytest.mark.id("tst_74z49t")
def test_one_worker():
    """One worker trains on every record once, in batches of size"""
    batches = worker_batches(N, SIZE, 1, 0, 0, 0)
    assert [len(batch) for batch in batches] == [SIZE] * (N // SIZE) + [N % SIZE]
    assert np.array_equal(np.sort(np.concatenate(batches)), np.arange(N))


@pytest.mark.id("tst_tck33f")
def test_turns():
    """Workers take turns through one order, which goes on from its start"""
    shares = [records(N, SIZE, 4, rank, 1, 2) for rank in range(4)]
    assert len({len(share) for share in shares}) == 1
    order = np.stack(shares, axis=1).ravel()
    assert np.array_equal(np.sort(order[:N]), np.arange(N))
    assert np.array_equal(order[N:], order[: len(order) - N])
    assert np.array_equal(order[:N], records(N, SIZE, 1, 0, 1, 2))


@pytest.mark.id("tst_8exdzj")
def test_batch_sizes():
    """Each worker's batches hold size rows, the last one smaller"""
    for rank in range(3):
        sizes = [len(batch) for batch in worker_batches(N, 16, 3, rank, 0, 0)]
        assert all(size == 16 for size in sizes[:-1])
        assert 0 < sizes[-1] <= 16


@pytest.mark.id("tst_uj52y9")
def test_reproducible():
    """The same arguments give the same batches"""
    first, again = records(N, SIZE, 3, 1, 4, 7), records(N, SIZE, 3, 1, 4, 7)
    assert np.array_equal(first, again)
