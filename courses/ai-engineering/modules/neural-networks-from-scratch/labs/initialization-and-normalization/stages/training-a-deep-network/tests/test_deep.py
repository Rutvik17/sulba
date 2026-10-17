import numpy as np
import pytest

from deep import make_layers

WIDTHS, BATCH, LR = (64, 48, 24, 10), 64, 0.3


@pytest.fixture(scope="module")
def office():
    """The training digits' pixels, on a scale of 0 to 1, and their digits."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    training = table[:, 0] == 0
    return table[training, 2:] / 16, table[training, 1].astype(np.int64)


def logits(layers, X, training):
    for layer in layers:
        X = layer.forward(X, training=training)
    return X


def loss(layers, X, digits):
    """The mean cross-entropy of the digits, read in evaluation."""
    shifted = logits(layers, X, False)
    shifted = shifted - shifted.max(axis=1, keepdims=True)
    log_sums = np.log(np.exp(shifted).sum(axis=1))
    return np.mean(log_sums - shifted[np.arange(len(digits)), digits])


def step(layers, X, digits):
    """A step of SGD on the batch's mean cross-entropy."""
    out = logits(layers, X, True)
    exps = np.exp(out - out.max(axis=1, keepdims=True))
    d = exps / exps.sum(axis=1, keepdims=True)
    d[np.arange(len(digits)), digits] -= 1
    d /= len(digits)
    for layer in reversed(layers):
        d = layer.backward(d)
    for layer in layers:
        for param, grad in zip(layer.params(), layer.grads(), strict=True):
            param -= LR * grad
    return d


def weights(layers):
    return [p for layer in layers for p in layer.params()]


@pytest.mark.id("tst_z0ac08")
def test_widths():
    """A linear layer between each pair of widths, in order, and a gradient for every
    parameter"""
    layers = make_layers(WIDTHS, np.random.default_rng(0))
    shapes = [p.shape for p in weights(layers) if p.ndim == 2]
    assert shapes == [(48, 64), (24, 48), (10, 24)]
    X = np.random.default_rng(1).normal(size=(5, 64))
    assert step(layers, X, np.arange(5)).shape == X.shape
    for layer in layers:
        assert [g.shape for g in layer.grads()] == [p.shape for p in layer.params()]


@pytest.mark.id("tst_b27y4z")
def test_other_widths(office):
    """A network of other widths trains: its loss falls by more than half"""
    X, digits = office
    rng = np.random.default_rng(2)
    layers = make_layers(WIDTHS, rng)
    before = loss(layers, X, digits)
    for _ in range(100):
        rows = rng.choice(len(digits), size=BATCH, replace=False)
        step(layers, X[rows], digits[rows])
    assert loss(layers, X, digits) < 0.5 * before


@pytest.mark.id("tst_rcww80")
def test_rng():
    """Every random number comes from rng: the same rng makes the same network"""
    first = weights(make_layers(WIDTHS, np.random.default_rng(3)))
    again = weights(make_layers(WIDTHS, np.random.default_rng(3)))
    other = weights(make_layers(WIDTHS, np.random.default_rng(4)))
    assert all(np.array_equal(a, b) for a, b in zip(first, again, strict=True))
    assert not all(np.array_equal(a, b) for a, b in zip(first, other, strict=True))
