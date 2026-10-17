import json
from pathlib import Path

import numpy as np
import pytest

from norms import LayerNorm

CASES = json.loads(Path("references/norms.json").read_text())["layer_norm"]
# PyTorch's results and yours may differ in the last digits, from working in another order.
RTOL, ATOL = 1e-10, 1e-12


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


def layer(case):
    found = LayerNorm(len(case["weight"]))
    found.weight[:] = case["weight"]
    found.bias[:] = case["bias"]
    return found


@pytest.mark.id("tst_i58tra")
def test_by_hand():
    """One sample normalized over its features, worked by hand"""
    norm = LayerNorm(4, eps=0.0)
    Y = norm.forward(np.array([[1.0, 2.0, 3.0, 6.0]]))
    # Its mean is 3 and its variance 3.5.
    assert np.allclose(Y, (np.array([[1.0, 2.0, 3.0, 6.0]]) - 3) / np.sqrt(3.5))


@pytest.mark.id("tst_toqsoi")
def test_outputs():
    """Each sample normalized over its features, then scaled and shifted, as PyTorch has
    it"""
    for case in CASES:
        assert close(layer(case).forward(np.array(case["X"])), case["Y"])


@pytest.mark.id("tst_t6ndnw")
def test_gradients():
    """The gradients with respect to the batch, the weight and the bias, as PyTorch has
    them"""
    for case in CASES:
        norm = layer(case)
        norm.forward(np.array(case["X"]))
        dX = norm.backward(np.array(case["dY"]))
        assert close(dX, case["dX"])
        assert close(norm.dweight, case["dweight"]) and close(norm.dbias, case["dbias"])


@pytest.mark.id("tst_ug6aer")
def test_constant_sample():
    """A sample whose features are all the same comes out as the bias"""
    norm = LayerNorm(3)
    norm.bias[:] = [0.5, -1.0, 2.0]
    assert np.allclose(norm.forward(np.full((1, 3), 7.0)), [[0.5, -1.0, 2.0]])


@pytest.mark.id("tst_u9me6g")
def test_alone_or_in_a_batch():
    """A sample reads the same alone as in its batch, in training and in evaluation"""
    case = CASES[0]
    X = np.array(case["X"])
    norm = layer(case)
    together = norm.forward(X, training=True)
    for row in range(len(X)):
        alone = norm.forward(X[row : row + 1], training=False)
        assert close(alone, together[row : row + 1])
