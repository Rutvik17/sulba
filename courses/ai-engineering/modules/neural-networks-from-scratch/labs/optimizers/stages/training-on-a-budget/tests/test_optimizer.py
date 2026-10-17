import numpy as np
import pytest

from optimizers import make_optimizer

BATCH = 64


def network(rng, widths):
    """A weight and a bias for each linear layer, drawn as torch.nn.Linear draws them."""
    params = []
    for inputs, outputs in zip(widths, widths[1:]):
        bound = 1 / np.sqrt(inputs)
        params.append(rng.uniform(-bound, bound, size=(outputs, inputs)))
        params.append(rng.uniform(-bound, bound, size=outputs))
    return params


def batches(rng, rows, steps):
    """steps batches of BATCH rows, in an order shuffled for each pass over them."""
    order = []
    while len(order) < steps * BATCH:
        order.extend(rng.permutation(rows))
    return [np.array(order[i * BATCH : (i + 1) * BATCH]) for i in range(steps)]


def forward(params, X):
    """Each layer's input, each ReLU's input, and the logits."""
    inputs, before = [X], []
    for number in range(0, len(params), 2):
        out = inputs[-1] @ params[number].T + params[number + 1]
        if number + 2 == len(params):
            return inputs, before, out
        before.append(out)
        inputs.append(np.maximum(out, 0.0))


def gradients(params, X, digits):
    """The mean cross-entropy's gradient with respect to each parameter."""
    inputs, before, logits = forward(params, X)
    exps = np.exp(logits - logits.max(axis=1, keepdims=True))
    d = exps / exps.sum(axis=1, keepdims=True)
    d[np.arange(len(digits)), digits] -= 1
    d /= len(digits)
    grads = [None] * len(params)
    for number in range(len(params) - 2, -1, -2):
        grads[number] = d.T @ inputs[number // 2]
        grads[number + 1] = d.sum(axis=0)
        if number:
            d = (d @ params[number]) * (before[number // 2 - 1] > 0)
    return grads


@pytest.fixture(scope="module")
def office():
    """The training digits' pixels, on a scale of 0 to 1, and their digits."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    training = table[:, 0] == 0
    return table[training, 2:] / 16, table[training, 1].astype(np.int64)


def loss(params, X, digits):
    logits = forward(params, X)[2]
    shifted = logits - logits.max(axis=1, keepdims=True)
    log_sums = np.log(np.exp(shifted).sum(axis=1))
    return np.mean(log_sums - shifted[np.arange(len(digits)), digits])


def train(params, optimizer, office, rng, steps):
    X, digits = office
    for rows in batches(rng, np.arange(len(digits)), steps):
        optimizer.step(gradients(params, X[rows], digits[rows]))


@pytest.mark.id("tst_gdh2vi")
def test_moves_the_network(office):
    """It moves the network's own weights, and the loss falls"""
    rng = np.random.default_rng(1)
    params = network(rng, (64, 64, 10))
    start = [p.copy() for p in params]
    train(params, make_optimizer(params), office, rng, 20)
    assert all(not np.array_equal(p, s) for p, s in zip(params, start, strict=True))
    assert loss(params, *office) < loss(start, *office)


@pytest.mark.id("tst_elcyjs")
def test_state_loads(office):
    """A saved state loaded into a new optimizer takes the same next step"""
    X, digits = office
    rng = np.random.default_rng(2)
    params = network(rng, (64, 32, 10))
    optimizer = make_optimizer(params)
    train(params, optimizer, office, rng, 5)
    copies = [p.copy() for p in params]
    resumed = make_optimizer(copies)
    resumed.load_state_dict(optimizer.state_dict())
    grads = gradients(params, X[:BATCH], digits[:BATCH])
    optimizer.step(grads)
    resumed.step(grads)
    for found, expected in zip(copies, params, strict=True):
        assert np.allclose(found, expected, rtol=1e-12, atol=1e-15)


@pytest.mark.id("tst_bf40vu")
def test_any_network(office):
    """It trains a network of another shape, three layers deep"""
    rng = np.random.default_rng(3)
    params = network(rng, (64, 32, 16, 10))
    start = [p.copy() for p in params]
    train(params, make_optimizer(params), office, rng, 50)
    assert loss(params, *office) < 0.8 * loss(start, *office)
