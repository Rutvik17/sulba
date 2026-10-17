import json
from pathlib import Path

import numpy as np
import pytest

from normalization import BatchNorm1d, LayerNorm

NORMS = json.loads(Path("references/norms.json").read_text())
RTOL, ATOL = 1e-10, 1e-12


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


def batch_norm(case):
    layer = BatchNorm1d(len(case["weight"]))
    layer.weight[:] = case["weight"]
    layer.bias[:] = case["bias"]
    return layer


@pytest.mark.id("tst_zaios5")
def test_evaluation():
    """In evaluation, the outputs PyTorch gives from the running estimates"""
    for case in NORMS["batch_norm"]:
        layer = batch_norm(case)
        layer.running_mean = np.array(case["steps"][-1]["running_mean"])
        layer.running_var = np.array(case["steps"][-1]["running_var"])
        Y = layer.forward(np.array(case["evaluation"]["X"]), training=False)
        assert close(Y, case["evaluation"]["Y"])


@pytest.mark.id("tst_xwzlfs")
def test_running_estimates():
    """The running estimates after each training batch, as PyTorch keeps them"""
    for case in NORMS["batch_norm"]:
        layer = batch_norm(case)
        for step in case["steps"]:
            layer.forward(np.array(step["X"]), training=True)
            assert close(layer.running_mean, step["running_mean"])
            assert close(layer.running_var, step["running_var"])


@pytest.mark.id("tst_hw9ipy")
def test_layer_norm():
    """Layer normalization's outputs for batches of samples, as PyTorch gives them"""
    for case in NORMS["layer_norm"]:
        layer = LayerNorm(len(case["weight"]))
        layer.weight[:] = case["weight"]
        layer.bias[:] = case["bias"]
        assert close(layer.forward(np.array(case["X"])), case["Y"])


@pytest.mark.id("tst_hx94kd")
def test_batch_gradients():
    """Batch normalization's gradients with respect to the batch, as PyTorch has them"""
    for case in NORMS["batch_norm"]:
        layer = batch_norm(case)
        for step in case["steps"]:
            layer.forward(np.array(step["X"]), training=True)
            assert close(layer.backward(np.array(step["dY"])), step["dX"])
