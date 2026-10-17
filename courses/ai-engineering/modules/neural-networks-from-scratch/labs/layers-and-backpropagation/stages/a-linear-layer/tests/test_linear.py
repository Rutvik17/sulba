import json
from pathlib import Path

import numpy as np
import pytest

from layers import Linear

CASES = json.loads(Path("references/linear.json").read_text())["cases"]
# PyTorch's results and yours may differ in the last digits, from summing in another order.
RTOL, ATOL = 1e-10, 1e-12


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


def by_hand():
    """One sample, two inputs and two outputs."""
    return Linear(np.array([[1.0, 2.0], [0.5, -1.0]]), np.array([0.25, 1.0]))


@pytest.mark.id("tst_8es1os")
def test_forward_by_hand():
    """One sample's outputs, worked by hand"""
    found = by_hand().forward(np.array([[3.0, -1.0]]))
    assert np.allclose(found, [[1.25, 3.5]], rtol=0, atol=1e-12)


@pytest.mark.id("tst_30kdp1")
def test_backward_by_hand():
    """That sample's gradients, worked by hand"""
    layer = by_hand()
    layer.forward(np.array([[3.0, -1.0]]))
    dX = layer.backward(np.array([[1.0, -2.0]]))
    assert np.allclose(dX, [[0.0, 4.0]], rtol=0, atol=1e-12)
    assert np.allclose(layer.dweight, [[3.0, -1.0], [-6.0, 2.0]], rtol=0, atol=1e-12)
    assert np.allclose(layer.dbias, [1.0, -2.0], rtol=0, atol=1e-12)


@pytest.mark.id("tst_2u1ac4")
def test_outputs_match_pytorch():
    """The same outputs as PyTorch's, in each recorded case"""
    for case in CASES:
        layer = Linear(np.array(case["weight"]), np.array(case["bias"]))
        assert close(layer.forward(np.array(case["X"])), case["Y"])


@pytest.mark.id("tst_wohpps")
def test_gradients_match_pytorch():
    """The same gradients as PyTorch's, in each recorded case"""
    for case in CASES:
        layer = Linear(np.array(case["weight"]), np.array(case["bias"]))
        layer.forward(np.array(case["X"]))
        assert close(layer.backward(np.array(case["dY"])), case["dX"])
        assert close(layer.dweight, case["dweight"])
        assert close(layer.dbias, case["dbias"])


@pytest.mark.id("tst_unurim")
def test_shapes():
    """Each gradient has the shape of what it's the gradient of"""
    for case in CASES:
        X, weight = np.array(case["X"]), np.array(case["weight"])
        layer = Linear(weight, np.array(case["bias"]))
        layer.forward(X)
        assert layer.backward(np.array(case["dY"])).shape == X.shape
        assert layer.dweight.shape == weight.shape
        assert layer.dbias.shape == (weight.shape[0],)


@pytest.mark.id("tst_rcfkad")
def test_inputs_kept():
    """The batch, the weight, the bias and the gradient it's given stay as they were"""
    case = CASES[-1]
    given = {key: np.array(case[key]) for key in ("X", "weight", "bias", "dY")}
    layer = Linear(given["weight"], given["bias"])
    layer.forward(given["X"])
    layer.backward(given["dY"])
    for key, value in given.items():
        assert np.array_equal(value, case[key]), key
