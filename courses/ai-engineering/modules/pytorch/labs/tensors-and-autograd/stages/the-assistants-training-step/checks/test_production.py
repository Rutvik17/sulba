import copy

import numpy as np
import pytest
import torch

from trainer import scale, start, step

HIDDEN, DIGITS, BATCH, LR = 32, 10, 64, 0.1
RTOL, ATOL = 1e-12, 1e-12


def office():
    """The training digits as NumPy arrays: pixels, scaled as the NumPy reader scales them, and
    the digits they show, and the test digits' pixels."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    train, test = table[table[:, 0] == 0], table[table[:, 0] == 2]
    pixels = np.ascontiguousarray(train[:, 2:])
    spread = pixels.std(axis=0)
    X = (pixels - pixels.mean(axis=0)) / np.where(spread > 0, spread, 1.0)
    return pixels, X, train[:, 1].astype(np.int64), np.ascontiguousarray(test[:, 2:])


def arrays(seed):
    """A start as the NumPy reader draws one."""
    rng = np.random.default_rng(seed)
    found = {}
    for layer, (inputs, outputs) in enumerate([(64, HIDDEN), (HIDDEN, DIGITS)], 1):
        bound = 1 / np.sqrt(inputs)
        found[f"w{layer}"] = rng.uniform(-bound, bound, size=(outputs, inputs))
        found[f"b{layer}"] = rng.uniform(-bound, bound, size=outputs)
    return found


def numpy_step(start_, X, digits, lr):
    """The NumPy reader's step from start_ on the batch."""
    hidden = X @ start_["w1"].T + start_["b1"]
    relu = np.where(hidden > 0, hidden, 0.0)
    z = relu @ start_["w2"].T + start_["b2"]
    shifted = z - z.max(axis=1, keepdims=True)
    dz = np.exp(shifted) / np.exp(shifted).sum(axis=1, keepdims=True)
    dz[np.arange(len(digits)), digits] -= 1
    dz /= len(digits)
    dhidden = np.where(hidden > 0, dz @ start_["w2"], 0.0)
    found = {
        "w1": dhidden.T @ X,
        "b1": dhidden.sum(axis=0),
        "w2": dz.T @ relu,
        "b2": dz.sum(axis=0),
    }
    return {name: start_[name] - lr * found[name] for name in start_}


def close(found, expected):
    return torch.allclose(
        found.detach(), torch.from_numpy(expected), rtol=RTOL, atol=ATOL
    )


def batch(X, digits, number):
    rows = slice(number * BATCH, (number + 1) * BATCH)
    return torch.from_numpy(X[rows]), torch.from_numpy(digits[rows])


@pytest.mark.id("tst_a80age")
def test_second_step():
    """A step after another, from its own batch's gradients"""
    _, X, digits, _ = office()
    begun = arrays(3)
    params = start(copy.deepcopy(begun))
    # A first step that moves nothing, then a step on another batch.
    step(params, *batch(X, digits, 0), 0.0)
    step(params, *batch(X, digits, 1), LR)
    expected = numpy_step(begun, X[BATCH : 2 * BATCH], digits[BATCH : 2 * BATCH], LR)
    assert close(params["w2"], expected["w2"]) and close(params["b2"], expected["b2"])


@pytest.mark.id("tst_o5p82o")
def test_every_layer_trains():
    """Every layer's step, as the NumPy reader takes it"""
    _, X, digits, _ = office()
    begun = arrays(4)
    params = start(copy.deepcopy(begun))
    step(params, *batch(X, digits, 2), LR)
    expected = numpy_step(
        begun, X[2 * BATCH : 3 * BATCH], digits[2 * BATCH : 3 * BATCH], LR
    )
    assert all(close(params[name], expected[name]) for name in expected)


@pytest.mark.id("tst_kjkzoo")
def test_scaled_as_numpy():
    """The pixels scaled as the NumPy reader scaled them"""
    pixels, _, _, test = office()
    spread = pixels.std(axis=0)
    expected = (test - pixels.mean(axis=0)) / np.where(spread > 0, spread, 1.0)
    found = scale(torch.from_numpy(test), torch.from_numpy(pixels))
    assert close(found, expected)


@pytest.mark.id("tst_apihzi")
def test_start_kept():
    """The office's start left as it was"""
    _, X, digits, _ = office()
    begun = arrays(5)
    kept = copy.deepcopy(begun)
    params = start(begun)
    for number in range(3):
        step(params, *batch(X, digits, number), LR)
    assert all(np.array_equal(begun[name], kept[name]) for name in kept)
