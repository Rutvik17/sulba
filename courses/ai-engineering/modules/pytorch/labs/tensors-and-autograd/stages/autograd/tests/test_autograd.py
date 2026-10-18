import numpy as np
import pytest
import torch

from network import gradients, logits, parameters, step

HIDDEN, DIGITS, BATCH, LR = 32, 10, 64, 0.1
# PyTorch and NumPy may differ in the last digits, from summing in another order.
RTOL, ATOL = 1e-12, 1e-12


def office():
    """The training digits scaled as the NumPy reader scales them, and the digits they show."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    train = table[table[:, 0] == 0]
    pixels, digits = train[:, 2:], train[:, 1].astype(np.int64)
    spread = pixels.std(axis=0)
    return (pixels - pixels.mean(axis=0)) / np.where(spread > 0, spread, 1.0), digits


def started(seed):
    """Weights and biases started as the NumPy reader starts them."""
    rng = np.random.default_rng(seed)
    start = {}
    for layer, (inputs, outputs) in enumerate([(64, HIDDEN), (HIDDEN, DIGITS)], 1):
        bound = 1 / np.sqrt(inputs)
        start[f"w{layer}"] = rng.uniform(-bound, bound, size=(outputs, inputs))
        start[f"b{layer}"] = rng.uniform(-bound, bound, size=outputs)
    return start


def numpy_pass(start, X, digits):
    """The NumPy reader's logits, loss and backward pass, as in the last module's layers."""
    hidden = X @ start["w1"].T + start["b1"]
    relu = np.where(hidden > 0, hidden, 0.0)
    z = relu @ start["w2"].T + start["b2"]
    shifted = z - z.max(axis=1, keepdims=True)
    log_probs = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
    rows = np.arange(len(digits))
    dz = np.exp(log_probs)
    dz[rows, digits] -= 1
    dz /= len(digits)
    dhidden = np.where(hidden > 0, dz @ start["w2"], 0.0)
    found = {
        "w1": dhidden.T @ X,
        "b1": dhidden.sum(axis=0),
        "w2": dz.T @ relu,
        "b2": dz.sum(axis=0),
    }
    return z, -log_probs[rows, digits].mean(), found


def numpy_step(start, X, digits, lr):
    """The NumPy reader's step: new weights and biases, and the loss before it."""
    _, loss, found = numpy_pass(start, X, digits)
    return {name: start[name] - lr * found[name] for name in start}, loss


def close(found, expected):
    return torch.allclose(found, torch.as_tensor(expected), rtol=RTOL, atol=ATOL)


@pytest.mark.id("tst_spxsst")
def test_parameters():
    """Parameters that autograd follows, copied from the start"""
    start = started(0)
    kept = {name: array.copy() for name, array in start.items()}
    params = parameters(start)
    for name, param in params.items():
        assert param.dtype == torch.float64 and param.requires_grad and param.is_leaf
        assert torch.equal(param.detach(), torch.from_numpy(kept[name]))
    with torch.no_grad():
        for param in params.values():
            param += 1
    assert all(np.array_equal(start[name], kept[name]) for name in start)


@pytest.mark.id("tst_v6j2s7")
def test_logits():
    """The NumPy reader's logits for a batch"""
    X, _ = office()
    start = started(1)
    expected, _, _ = numpy_pass(start, X[:BATCH], np.zeros(BATCH, dtype=np.int64))
    assert close(logits(parameters(start), torch.from_numpy(X[:BATCH])), expected)


@pytest.mark.id("tst_g29ftz")
def test_gradients():
    """The NumPy reader's gradients for a batch"""
    X, digits = office()
    for seed, rows in [(2, slice(0, BATCH)), (3, slice(BATCH, 3 * BATCH))]:
        start = started(seed)
        _, _, expected = numpy_pass(start, X[rows], digits[rows])
        found = gradients(
            parameters(start), torch.from_numpy(X[rows]), torch.from_numpy(digits[rows])
        )
        assert set(found) == set(expected)
        assert all(close(found[name], expected[name]) for name in expected)


@pytest.mark.id("tst_d8hh0y")
def test_gradients_twice():
    """The same gradients twice, and no .grad left behind"""
    X, digits = office()
    params = parameters(started(4))
    batch = torch.from_numpy(X[:BATCH]), torch.from_numpy(digits[:BATCH])
    first, second = gradients(params, *batch), gradients(params, *batch)
    assert all(torch.equal(first[name], second[name]) for name in first)
    assert all(param.grad is None for param in params.values())


@pytest.mark.id("tst_zcj847")
def test_step():
    """A step as the NumPy reader takes it"""
    X, digits = office()
    start = started(5)
    expected, expected_loss = numpy_step(start, X[:BATCH], digits[:BATCH], LR)
    params = parameters(start)
    loss = step(
        params, torch.from_numpy(X[:BATCH]), torch.from_numpy(digits[:BATCH]), LR
    )
    assert isinstance(loss, float) and loss == pytest.approx(
        expected_loss, rel=RTOL, abs=ATOL
    )
    assert all(close(params[name].detach(), expected[name]) for name in expected)


@pytest.mark.id("tst_jtgmju")
def test_steps():
    """Steps after steps, as the NumPy reader takes them"""
    X, digits = office()
    expected = started(6)
    params = parameters(expected)
    for begin in range(0, 4 * BATCH, BATCH):
        rows = slice(begin, begin + BATCH)
        expected, _ = numpy_step(expected, X[rows], digits[rows], LR)
        step(params, torch.from_numpy(X[rows]), torch.from_numpy(digits[rows]), LR)
    for name, param in params.items():
        assert param.is_leaf and param.requires_grad
        assert close(param.detach(), expected[name])
