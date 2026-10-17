import json
from pathlib import Path

import numpy as np
import pytest

from norms import BatchNorm1d

CASES = json.loads(Path("references/norms.json").read_text())["batch_norm"]
# PyTorch's results and yours may differ in the last digits, from working in another order.
RTOL, ATOL = 1e-10, 1e-12


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


def replay(case):
    """A layer with the case's weight and bias, and what it gives at each training step."""
    layer = BatchNorm1d(len(case["weight"]))
    layer.weight[:] = case["weight"]
    layer.bias[:] = case["bias"]
    found = []
    for step in case["steps"]:
        Y = layer.forward(np.array(step["X"]), training=True)
        dX = layer.backward(np.array(step["dY"]))
        found.append(
            (
                Y,
                dX,
                layer.dweight,
                layer.dbias,
                layer.running_mean.copy(),
                layer.running_var.copy(),
            )
        )
    return layer, found


@pytest.mark.id("tst_meszu5")
def test_by_hand():
    """A batch of two, normalized, and its running estimates, worked by hand"""
    layer = BatchNorm1d(2, eps=0.0)
    Y = layer.forward(np.array([[1.0, 10.0], [3.0, 30.0]]))
    assert np.allclose(Y, [[-1.0, -1.0], [1.0, 1.0]])
    assert np.allclose(layer.running_mean, [0.2, 2.0])
    # Each feature's unbiased variance, 2 and 200, mixed in at a tenth.
    assert np.allclose(layer.running_var, [0.9 + 0.2, 0.9 + 20.0])


@pytest.mark.id("tst_9yjj59")
def test_training():
    """Each feature normalized over its batch, then scaled and shifted, as PyTorch has it"""
    for case in CASES:
        _, found = replay(case)
        for (Y, *_), step in zip(found, case["steps"], strict=True):
            assert close(Y, step["Y"])


@pytest.mark.id("tst_xyra1p")
def test_gradients():
    """The gradients with respect to the batch, the weight and the bias, as PyTorch has
    them"""
    for case in CASES:
        _, found = replay(case)
        for (_, dX, dweight, dbias, *_), step in zip(found, case["steps"], strict=True):
            assert close(dX, step["dX"])
            assert close(dweight, step["dweight"]) and close(dbias, step["dbias"])


@pytest.mark.id("tst_2qszi6")
def test_running_estimates():
    """The running mean and variance after each training batch, as PyTorch keeps them"""
    for case in CASES:
        _, found = replay(case)
        for (*_, mean, var), step in zip(found, case["steps"], strict=True):
            assert close(mean, step["running_mean"]) and close(var, step["running_var"])


@pytest.mark.id("tst_dapr0g")
def test_evaluation():
    """Evaluation normalizes with the running estimates, as PyTorch does, and leaves them
    as they were"""
    for case in CASES:
        layer, _ = replay(case)
        mean, var = layer.running_mean.copy(), layer.running_var.copy()
        Y = layer.forward(np.array(case["evaluation"]["X"]), training=False)
        assert close(Y, case["evaluation"]["Y"])
        assert np.array_equal(layer.running_mean, mean)
        assert np.array_equal(layer.running_var, var)


@pytest.mark.id("tst_6o60or")
def test_params():
    """params and grads give the weight and the bias, and their gradients"""
    layer = BatchNorm1d(3)
    layer.forward(np.arange(12.0).reshape(4, 3))
    layer.backward(np.ones((4, 3)))
    assert layer.params()[0] is layer.weight and layer.params()[1] is layer.bias
    assert np.allclose(layer.grads()[1], [4.0, 4.0, 4.0])
