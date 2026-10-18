import numpy as np
import pytest

from network import loss_and_grads, network
from train import train

LR = 0.5


@pytest.fixture(scope="module")
def office():
    """The pixels with each digit's row number after them, the digits, and their sets."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    numbered = np.column_stack([table[:, 2:] / 16, np.arange(len(table))])
    return numbered, table[:, 1].astype(np.int64), table[:, 0]


def noting(seen):
    """A loss_and_grads that notes each batch's row numbers, digits and gradients."""

    def loss_and_grads_of(params, pixels, labels):
        loss, grads = loss_and_grads(params, pixels[:, :-1], labels)
        seen.append((pixels[:, -1].astype(np.int64), labels, [g.copy() for g in grads]))
        return loss, grads

    return loss_and_grads_of


def trained(office, seen, **settings):
    params = network(np.random.default_rng(0))
    start = [param.copy() for param in params]
    X, digits, sets = office
    train(
        params,
        X,
        digits,
        sets,
        np.random.default_rng(1),
        lr=LR,
        loss_and_grads=noting(seen),
        **settings,
    )
    return start, params


@pytest.mark.id("tst_i5qb8f")
def test_pairs(office):
    """Every batch pairs each digit with its own pixels"""
    seen = []
    trained(office, seen, steps=50)
    _, digits, _ = office
    assert all(np.array_equal(digits[rows], labels) for rows, labels, _ in seen)


@pytest.mark.id("tst_jcj3x5")
def test_training_digits(office):
    """No test digit is trained on"""
    seen = []
    trained(office, seen, steps=50)
    _, _, sets = office
    assert all(np.all(sets[rows] == 0) for rows, _, _ in seen)


@pytest.mark.id("tst_44dv2k")
def test_accumulated(office):
    """Each step is the mean of its batches' gradients, as one batch of their combined size
    would give it"""
    seen = []
    start, params = trained(office, seen, steps=4, accumulate=2, max_norm=1e9)
    expected = [param.copy() for param in start]
    for step in range(4):
        pair = [grads for _, _, grads in seen[2 * step : 2 * step + 2]]
        for number, param in enumerate(expected):
            param -= LR * (pair[0][number] + pair[1][number]) / 2
    for found, wanted in zip(params, expected, strict=True):
        assert np.allclose(found, wanted, rtol=1e-12, atol=1e-15)


@pytest.mark.id("tst_wtuvt8")
def test_clipped_together(office):
    """A step's gradients are clipped together, as clip_grad_norm_ clips them"""
    seen = []
    start, params = trained(office, seen, steps=1, accumulate=1, max_norm=0.05)
    grads = seen[0][2]
    total = np.sqrt(sum(np.sum(grad**2) for grad in grads))
    scale = min(0.05 / (total + 1e-6), 1.0)
    for found, before, grad in zip(params, start, grads, strict=True):
        assert np.allclose(found, before - LR * scale * grad, rtol=1e-12, atol=1e-15)
