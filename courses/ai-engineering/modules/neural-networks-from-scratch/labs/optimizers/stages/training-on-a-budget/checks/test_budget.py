import numpy as np
import pytest

from optimizers import make_optimizer

# The office's network and its training, and what it must read of new writers' digits.
WIDTHS, BATCH, BUDGET, TARGET = (64, 64, 10), 64, 300, 0.93


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
    """The pixels, on a scale of 0 to 1, the digits, and the set each digit is in."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    return table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]


@pytest.fixture(scope="module")
def straight(office):
    """The network's weights at the start, its batches, and its weights after training
    straight through the budget."""
    X, digits, sets = office
    rng = np.random.default_rng(0)
    params = network(rng, WIDTHS)
    start = [p.copy() for p in params]
    plan = batches(rng, np.flatnonzero(sets == 0), BUDGET)
    optimizer = make_optimizer(params)
    for rows in plan:
        optimizer.step(gradients(params, X[rows], digits[rows]))
    return start, plan, params


@pytest.mark.id("tst_8o5bwg")
def test_new_writers(office, straight, record_property):
    """93% of new writers' digits in 300 steps"""
    X, digits, sets = office
    test = sets == 2
    _, _, params = straight
    share = np.mean(forward(params, X[test])[2].argmax(axis=1) == digits[test])
    record_property("note", f"{share:.1%} right")
    assert share >= TARGET


@pytest.mark.id("tst_qr4yi1")
def test_resumed(office, straight, record_property):
    """Resumed as if it never stopped"""
    X, digits, _ = office
    start, plan, finished = straight
    params = [p.copy() for p in start]
    optimizer = make_optimizer(params)
    half = BUDGET // 2
    for rows in plan[:half]:
        optimizer.step(gradients(params, X[rows], digits[rows]))
    state = optimizer.state_dict()
    copies = [p.copy() for p in params]
    resumed = make_optimizer(copies)
    resumed.load_state_dict(state)
    for rows in plan[half:]:
        resumed.step(gradients(copies, X[rows], digits[rows]))
    largest = max(np.max(np.abs(c - f)) for c, f in zip(copies, finished, strict=True))
    record_property("note", f"largest difference {largest:.1e}")
    for found, expected in zip(copies, finished, strict=True):
        assert np.allclose(found, expected, rtol=1e-12, atol=1e-15)
