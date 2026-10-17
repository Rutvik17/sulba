import numpy as np
import pytest

from deep import make_layers

# The office's deep network and its training, and what it must read of new writers' digits.
WIDTHS, BATCH, STEPS, LR, TARGET = (64,) + (32,) * 8 + (10,), 64, 200, 0.3, 0.9
# How many test digits are read alone, one at a time.
ALONE = 50


def batches(rng, rows, steps):
    """steps batches of BATCH rows, in an order shuffled for each pass over them."""
    order = []
    while len(order) < steps * BATCH:
        order.extend(rng.permutation(rows))
    return [np.array(order[i * BATCH : (i + 1) * BATCH]) for i in range(steps)]


def logits(layers, X, training):
    for layer in layers:
        X = layer.forward(X, training=training)
    return X


@pytest.fixture(scope="module")
def office():
    """The pixels, on a scale of 0 to 1, the digits, and the set each digit is in."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    return table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]


@pytest.fixture(scope="module")
def trained(office):
    """The office's network, trained by SGD on the mean cross-entropy of each batch."""
    X, digits, sets = office
    rng = np.random.default_rng(0)
    layers = make_layers(WIDTHS, rng)
    for rows in batches(rng, np.flatnonzero(sets == 0), STEPS):
        out = logits(layers, X[rows], True)
        exps = np.exp(out - out.max(axis=1, keepdims=True))
        d = exps / exps.sum(axis=1, keepdims=True)
        d[np.arange(BATCH), digits[rows]] -= 1
        d /= BATCH
        for layer in reversed(layers):
            d = layer.backward(d)
        for layer in layers:
            for param, grad in zip(layer.params(), layer.grads(), strict=True):
                param -= LR * grad
    return layers


@pytest.mark.id("tst_pnoj0g")
def test_new_writers(office, trained, record_property):
    """90% of new writers' digits"""
    X, digits, sets = office
    test = sets == 2
    share = np.mean(logits(trained, X[test], False).argmax(axis=1) == digits[test])
    record_property("note", f"{share:.1%} right")
    assert share >= TARGET


@pytest.mark.id("tst_57ztrf")
def test_alone(office, trained, record_property):
    """A digit reads the same alone"""
    X, _, sets = office
    test = X[sets == 2]
    together = logits(trained, test, False)
    largest = max(
        np.max(np.abs(logits(trained, test[row : row + 1], False)[0] - together[row]))
        for row in range(ALONE)
    )
    record_property("note", f"largest difference {largest:.1e}")
    assert largest <= 1e-9 * max(1.0, np.max(np.abs(together[:ALONE])))
