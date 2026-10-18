import numpy as np
import pytest
import torch

from trainer import forward, scale, start, step

HIDDEN, DIGITS, BATCH, LR = 32, 10, 64, 0.1


def office():
    """The training digits' pixels and the digits they show."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    train = table[table[:, 0] == 0]
    pixels = torch.from_numpy(np.ascontiguousarray(train[:, 2:]))
    return pixels, torch.from_numpy(train[:, 1].astype(np.int64))


def arrays(seed):
    """A start as the NumPy reader draws one."""
    rng = np.random.default_rng(seed)
    found = {}
    for layer, (inputs, outputs) in enumerate([(64, HIDDEN), (HIDDEN, DIGITS)], 1):
        bound = 1 / np.sqrt(inputs)
        found[f"w{layer}"] = rng.uniform(-bound, bound, size=(outputs, inputs))
        found[f"b{layer}"] = rng.uniform(-bound, bound, size=outputs)
    return found


@pytest.mark.id("tst_2ywbmf")
def test_start():
    """Weights and biases that need gradients"""
    params = start(arrays(0))
    assert set(params) == {"w1", "b1", "w2", "b2"}
    assert all(
        param.requires_grad and param.dtype == torch.float64
        for param in params.values()
    )


@pytest.mark.id("tst_i911ub")
def test_scale():
    """Scaled training pixels with a mean of 0"""
    pixels, _ = office()
    means = scale(pixels, pixels).mean(dim=0)
    assert torch.allclose(means, torch.zeros_like(means), atol=1e-12)


@pytest.mark.id("tst_8ye2fy")
def test_logits():
    """A logit for each digit"""
    pixels, _ = office()
    found = forward(start(arrays(1)), scale(pixels[:BATCH], pixels))
    assert found.shape == (BATCH, DIGITS)


@pytest.mark.id("tst_1n2zba")
def test_steps_lower_the_loss():
    """Steps that lower the loss on a batch"""
    pixels, digits = office()
    params = start(arrays(2))
    X = scale(pixels[:BATCH], pixels)
    first = step(params, X, digits[:BATCH], LR)
    for _ in range(3):
        last = step(params, X, digits[:BATCH], LR)
    assert last < first
