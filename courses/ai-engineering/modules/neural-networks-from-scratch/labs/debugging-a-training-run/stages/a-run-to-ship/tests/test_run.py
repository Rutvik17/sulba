import numpy as np
import pytest

from network import loss_and_grads
from run import train_office


def counting(seen):
    """A loss_and_grads that notes the size of each batch it's given."""

    def loss_and_grads_of(params, X, digits):
        seen.append(len(X))
        return loss_and_grads(params, X, digits)

    return loss_and_grads_of


@pytest.mark.id("tst_qunwc3")
def test_report():
    """The report gives the run's learning rate, batch, batches and validation share"""
    _, report = train_office(2, batches=20)
    assert set(report) == {"lr", "batch", "batches", "validation"}
    assert report["lr"] > 0 and 0 <= report["validation"] <= 1


@pytest.mark.id("tst_kv28m4")
def test_reproducible():
    """The same seed trains the same network, with the same report"""
    first, report = train_office(3, batches=20)
    again, report_again = train_office(3, batches=20)
    assert report == report_again
    assert all(np.array_equal(a, b) for a, b in zip(first, again, strict=True))


@pytest.mark.id("tst_3i8x8s")
def test_seeds():
    """Another seed trains another network"""
    first, _ = train_office(3, batches=20)
    other, _ = train_office(4, batches=20)
    assert not all(np.array_equal(a, b) for a, b in zip(first, other, strict=True))


@pytest.mark.id("tst_9dwx9d")
def test_batches():
    """It trains on the batches it's asked for, through the loss_and_grads it's given"""
    seen = []
    _, report = train_office(5, batches=20, loss_and_grads=counting(seen))
    assert len(seen) == 20 == report["batches"]
