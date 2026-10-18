import math

import numpy as np
import pytest

from network import first_below, forward, learn_by_heart, network, start_loss


@pytest.fixture(scope="module")
def office():
    """The training digits' pixels, on a scale of 0 to 1, and their digits."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    training = table[:, 0] == 0
    return table[training, 2:] / 16, table[training, 1].astype(np.int64)


def flipped(params, X, digits):
    """The loss and gradients with each ReLU's mask flipped, a broken backward pass."""
    inputs, before, logits = forward(params, X)
    shifted = logits - logits.max(axis=1, keepdims=True)
    log_sums = np.log(np.exp(shifted).sum(axis=1))
    loss = np.mean(log_sums - shifted[np.arange(len(digits)), digits])
    d = np.exp(shifted - log_sums[:, None])
    d[np.arange(len(digits)), digits] -= 1
    d /= len(digits)
    grads = [None] * len(params)
    for number in range(len(params) - 2, -1, -2):
        grads[number] = d.T @ inputs[number // 2]
        grads[number + 1] = d.sum(axis=0)
        if number:
            d = (d @ params[number]) * (before[number // 2 - 1] <= 0)
    return loss, grads


@pytest.mark.id("tst_1ssavl")
def test_start_loss(office):
    """The office's network starts near ln 10, the loss of a guess among ten digits"""
    loss, expected = start_loss(network(np.random.default_rng(0)), *office)
    assert expected == pytest.approx(math.log(10))
    assert abs(loss - expected) < 0.05


@pytest.mark.id("tst_9sslma")
def test_start_too_large(office):
    """A last layer started far too large starts far above ln 10"""
    params = network(np.random.default_rng(0))
    params[-2] *= 30
    params[-1] *= 30
    loss, expected = start_loss(params, *office)
    assert loss > 2 * expected


@pytest.mark.id("tst_3n2gkg")
def test_classes(office):
    """The loss to expect comes from the network's number of classes"""
    X, digits = office
    keep = digits < 3
    params = network(np.random.default_rng(1), (64, 16, 3))
    _, expected = start_loss(params, X[keep], digits[keep])
    assert expected == pytest.approx(math.log(3))


@pytest.mark.id("tst_mctabz")
def test_by_heart(office):
    """The office's network learns a batch of 32 digits by heart"""
    X, digits = office
    params = network(np.random.default_rng(0))
    losses = learn_by_heart(params, X[:32], digits[:32])
    assert len(losses) == 300
    assert losses[0] == pytest.approx(start_loss(params, X[:32], digits[:32])[0])
    assert first_below(losses) is not None


@pytest.mark.id("tst_ccgh6s")
def test_copy(office):
    """Learning by heart leaves the network as it was"""
    X, digits = office
    params = network(np.random.default_rng(0))
    before = [param.copy() for param in params]
    learn_by_heart(params, X[:32], digits[:32], steps=5)
    assert all(np.array_equal(p, b) for p, b in zip(params, before, strict=True))


@pytest.mark.id("tst_d6a6ef")
def test_broken_gradients(office):
    """A network with a broken backward pass never learns the batch by heart"""
    X, digits = office
    losses = learn_by_heart(
        network(np.random.default_rng(0)), X[:32], digits[:32], loss_and_grads=flipped
    )
    assert first_below(losses) is None


@pytest.mark.id("tst_sjqva8")
def test_shuffled_labels(office):
    """It learns 32 shuffled labels by heart too"""
    X, digits = office
    shuffled = np.random.default_rng(1).permutation(digits[:32])
    losses = learn_by_heart(network(np.random.default_rng(0)), X[:32], shuffled)
    assert first_below(losses) is not None


@pytest.mark.id("tst_fuuxsr")
def test_first_below():
    """The first step below the line, counting from 1, or None"""
    assert first_below([2.3, 0.5, 0.009, 0.001]) == 3
    assert first_below([2.3, 0.5], below=0.6) == 2
    assert first_below([2.3, 0.5]) is None
