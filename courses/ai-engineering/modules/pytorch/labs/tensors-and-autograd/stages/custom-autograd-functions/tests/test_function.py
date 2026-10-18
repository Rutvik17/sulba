import numpy as np
import pytest
import torch
import torch.nn.functional as F

from network import cross_entropy, logits, parameters

DIGITS, BATCH = 10, 64
RTOL, ATOL = 1e-12, 1e-12


def batch(seed, rows=BATCH, scale=3.0):
    """Logits that autograd follows, in float64, and the digits they're scored against."""
    generator = torch.Generator().manual_seed(seed)
    found = scale * torch.randn(rows, DIGITS, generator=generator, dtype=torch.float64)
    return found.requires_grad_(), torch.randint(
        0, DIGITS, (rows,), generator=generator
    )


def close(found, expected):
    return torch.allclose(found, torch.as_tensor(expected), rtol=RTOL, atol=ATOL)


@pytest.mark.id("tst_x2bf97")
def test_loss():
    """The loss F.cross_entropy gives"""
    for seed in range(3):
        z, digits = batch(seed)
        assert close(cross_entropy(z, digits), F.cross_entropy(z, digits))


@pytest.mark.id("tst_z6nw7v")
def test_gradient():
    """The gradient autograd gives F.cross_entropy"""
    for seed in range(3):
        z, digits = batch(seed)
        (found,) = torch.autograd.grad(cross_entropy(z, digits), z)
        (expected,) = torch.autograd.grad(F.cross_entropy(z, digits), z)
        assert close(found, expected)


@pytest.mark.id("tst_onxe5a")
def test_gradcheck():
    """A backward pass that gradcheck accepts"""
    z, digits = batch(3, rows=6)
    assert torch.autograd.gradcheck(lambda logits: cross_entropy(logits, digits), (z,))


@pytest.mark.id("tst_ym4j35")
def test_confident_logits():
    """A finite loss and gradient for logits in the thousands"""
    z, digits = batch(4, scale=1000.0)
    loss = cross_entropy(z, digits)
    (found,) = torch.autograd.grad(loss, z)
    assert close(loss, F.cross_entropy(z, digits))
    assert torch.isfinite(found).all()


@pytest.mark.id("tst_s9ys1k")
def test_gradient_flowing_in():
    """The gradient that flows in, multiplied through"""
    z, digits = batch(5)
    (plain,) = torch.autograd.grad(cross_entropy(z, digits), z)
    (tripled,) = torch.autograd.grad(3 * cross_entropy(z, digits), z)
    assert close(tripled, 3 * plain)


@pytest.mark.id("tst_xjfw34")
def test_office_batch():
    """The NumPy reader's loss and gradients for a batch of the office's digits"""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)[:BATCH]
    X, digits = table[:, 2:] / 16, table[:, 1].astype(np.int64)
    rng = np.random.default_rng(7)
    start = {}
    for layer, (inputs, outputs) in enumerate([(X.shape[1], 32), (32, DIGITS)], 1):
        bound = 1 / np.sqrt(inputs)
        start[f"w{layer}"] = rng.uniform(-bound, bound, size=(outputs, inputs))
        start[f"b{layer}"] = rng.uniform(-bound, bound, size=outputs)
    hidden = X @ start["w1"].T + start["b1"]
    relu = np.where(hidden > 0, hidden, 0.0)
    z = relu @ start["w2"].T + start["b2"]
    shifted = z - z.max(axis=1, keepdims=True)
    log_probs = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
    dz = np.exp(log_probs)
    dz[np.arange(BATCH), digits] -= 1
    dz /= BATCH
    dhidden = np.where(hidden > 0, dz @ start["w2"], 0.0)
    expected = {
        "w1": dhidden.T @ X,
        "b1": dhidden.sum(axis=0),
        "w2": dz.T @ relu,
        "b2": dz.sum(axis=0),
    }
    params = parameters(start)
    loss = cross_entropy(logits(params, torch.from_numpy(X)), torch.from_numpy(digits))
    found = torch.autograd.grad(loss, list(params.values()))
    assert close(loss, -log_probs[np.arange(BATCH), digits].mean())
    assert all(
        close(grad, expected[name]) for name, grad in zip(params, found, strict=True)
    )
