import numpy as np
import pytest

from sampling import worker_batches

N, SIZE = 455, 32
WORKERS, EPOCHS, SEEDS = range(1, 17), range(3), range(10)


def shares(n, size, workers, epoch, seed):
    """Each worker's batches."""
    return [
        worker_batches(n, size, workers, rank, epoch, seed) for rank in range(workers)
    ]


@pytest.mark.id("tst_c7gpnn")
def test_every_record(record_property):
    """Every record, every epoch"""
    for workers in WORKERS:
        for epoch in EPOCHS:
            found = shares(N, SIZE, workers, epoch, 0)
            rows = np.concatenate([batch for share in found for batch in share])
            counts = np.bincount(rows, minlength=N)
            missing, again = int(np.sum(counts == 0)), int(np.sum(counts) - N)
            needed = workers * -(-N // workers) - N
            if missing or again > needed:
                record_property(
                    "note",
                    f"On {workers} workers in epoch {epoch}: {missing} records left out, "
                    f"and {again} used again where equal shares need at most {needed}",
                )
                pytest.fail("An epoch left a record out, or used too many again.")


@pytest.mark.id("tst_n4svig")
def test_same_steps(record_property):
    """The same number of steps on every worker"""
    for workers in WORKERS:
        for size in (8, 16, 32, 64):
            found = shares(N, size, workers, 0, 0)
            batches = [len(share) for share in found]
            rows = [sum(len(batch) for batch in share) for share in found]
            if len(set(batches)) > 1 or len(set(rows)) > 1:
                record_property(
                    "note",
                    f"On {workers} workers with batches of {size}: "
                    f"{', '.join(map(str, batches))} batches",
                )
                pytest.fail("The workers got different numbers of records or batches.")


@pytest.mark.id("tst_ishkjv")
def test_new_orders(record_property):
    """A new order for every seed and epoch"""
    seen = {}
    for seed in SEEDS:
        for epoch in range(len(SEEDS)):
            order = tuple(
                np.concatenate(worker_batches(N, SIZE, 1, 0, epoch, seed)).tolist()
            )
            if order in seen:
                record_property(
                    "note",
                    f"Seed {seed} in epoch {epoch} drew the same order as seed "
                    f"{seen[order][0]} in epoch {seen[order][1]}",
                )
                pytest.fail("Two seeds and epochs gave the same order.")
            seen[order] = (seed, epoch)


@pytest.mark.id("tst_kv0noa")
def test_more_workers_than_records(record_property):
    """More workers than records"""
    for n, workers in ((3, 8), (5, 8), (1, 4)):
        found = shares(n, 4, workers, 0, 0)
        sizes = [[len(batch) for batch in share] for share in found]
        if any(share != [1] for share in sizes):
            empty = sum(1 for share in sizes if sum(share) == 0)
            record_property(
                "note",
                f"{n} records on {workers} workers: {empty} workers got no records",
            )
            pytest.fail("A worker didn't get exactly one record.")
        rows = np.concatenate([np.concatenate(share) for share in found])
        assert np.array_equal(np.unique(rows), np.arange(n))
