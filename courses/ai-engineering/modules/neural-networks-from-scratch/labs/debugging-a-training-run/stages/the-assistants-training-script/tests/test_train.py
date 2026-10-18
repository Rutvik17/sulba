import numpy as np
import pytest

from network import loss_and_grads, network
from train import train


@pytest.fixture(scope="module")
def office():
    """The pixels, on a scale of 0 to 1, the digits, and the set each digit is in."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    return table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]


@pytest.mark.id("tst_sg3js6")
def test_losses(office):
    """It gives a loss for each batch of each step"""
    losses = train(
        network(np.random.default_rng(0)), *office, np.random.default_rng(1), steps=3
    )
    assert len(losses) == 6


@pytest.mark.id("tst_uz80fg")
def test_in_place(office):
    """It trains the network's own arrays"""
    params = network(np.random.default_rng(0))
    held = [param.copy() for param in params]
    train(params, *office, np.random.default_rng(1), steps=2)
    assert all(not np.array_equal(p, h) for p, h in zip(params, held, strict=True))


@pytest.mark.id("tst_v5of8i")
def test_same_rng(office):
    """The same random numbers train the same network"""
    first, again = network(np.random.default_rng(0)), network(np.random.default_rng(0))
    train(first, *office, np.random.default_rng(1), steps=5)
    train(again, *office, np.random.default_rng(1), steps=5)
    assert all(np.array_equal(a, b) for a, b in zip(first, again, strict=True))


@pytest.mark.id("tst_agdn95")
def test_validation_out(office):
    """No validation digit is trained on"""
    X, digits, sets = office
    marked = X.copy()
    marked[sets == 1] = -1.0
    seen = []

    def noting(params, pixels, labels):
        seen.append(pixels)
        return loss_and_grads(params, pixels, labels)

    train(
        network(np.random.default_rng(0)),
        marked,
        digits,
        sets,
        np.random.default_rng(1),
        steps=20,
        loss_and_grads=noting,
    )
    assert all(np.all(pixels >= 0) for pixels in seen)


@pytest.mark.id("tst_lp36aq")
def test_clipping(office):
    """A step's gradient is clipped to max_norm"""

    def steep(params, pixels, labels):
        return 1.0, [np.full_like(params[0], 10.0)]

    params = [np.zeros(4)]
    train(
        params,
        *office,
        np.random.default_rng(1),
        steps=1,
        lr=1.0,
        accumulate=1,
        max_norm=0.5,
        loss_and_grads=steep,
    )
    assert np.linalg.norm(params[0]) == pytest.approx(0.5, rel=1e-5)
