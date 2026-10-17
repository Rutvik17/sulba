import json
from pathlib import Path

import numpy as np
import pytest

from layers import ReLU, cross_entropy

RECORDED = json.loads(Path("references/activations.json").read_text())
# PyTorch's results and yours may differ in the last digits, from summing in another order.
RTOL, ATOL = 1e-10, 1e-12


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


@pytest.mark.id("tst_blly5a")
def test_relu_by_hand():
    """ReLU on a value below 0, at 0 and above 0, worked by hand"""
    relu = ReLU()
    assert np.array_equal(relu.forward(np.array([[-2.0, 0.0, 3.0]])), [[0.0, 0.0, 3.0]])
    assert np.array_equal(relu.backward(np.array([[5.0, 6.0, 7.0]])), [[0.0, 0.0, 7.0]])


@pytest.mark.id("tst_o4refr")
def test_relu_matches_pytorch():
    """The same outputs and gradients as torch.relu, with zeros among the inputs"""
    for case in RECORDED["relu"]:
        relu = ReLU()
        assert close(relu.forward(np.array(case["X"])), case["Y"])
        assert close(relu.backward(np.array(case["dY"])), case["dX"])


@pytest.mark.id("tst_zfwab7")
def test_equal_logits():
    """Equal logits give a loss of log 10, and the gradient worked by hand"""
    labels = np.array([0, 3, 9, 3])
    loss, dlogits = cross_entropy(np.zeros((4, 10)), labels)
    assert loss == pytest.approx(np.log(10), rel=1e-12)
    expected = np.full((4, 10), 0.1)
    expected[np.arange(4), labels] -= 1
    assert np.allclose(dlogits, expected / 4, rtol=0, atol=1e-15)


@pytest.mark.id("tst_ia100m")
def test_cross_entropy_matches_pytorch():
    """The same loss and gradient as PyTorch's cross_entropy, for batches of 1 to 32"""
    for case in RECORDED["cross_entropy"][:3]:
        loss, dlogits = cross_entropy(
            np.array(case["logits"]), np.array(case["labels"])
        )
        assert loss == pytest.approx(case["loss"], rel=RTOL, abs=ATOL)
        assert close(dlogits, case["dlogits"])


@pytest.mark.id("tst_mjveti")
def test_confident_logits():
    """Finite, and the same as PyTorch's, for logits in the thousands"""
    case = RECORDED["cross_entropy"][3]
    loss, dlogits = cross_entropy(np.array(case["logits"]), np.array(case["labels"]))
    assert np.isfinite(loss) and np.all(np.isfinite(dlogits))
    assert loss == pytest.approx(case["loss"], rel=RTOL, abs=ATOL)
    assert close(dlogits, case["dlogits"])


@pytest.mark.id("tst_xd3441")
def test_inputs_kept():
    """The logits, the labels and ReLU's inputs stay as they were"""
    case = RECORDED["cross_entropy"][1]
    logits, labels = np.array(case["logits"]), np.array(case["labels"])
    cross_entropy(logits, labels)
    assert np.array_equal(logits, case["logits"])
    assert np.array_equal(labels, case["labels"])
    X = np.array(RECORDED["relu"][1]["X"])
    relu = ReLU()
    relu.forward(X)
    relu.backward(np.ones_like(X))
    assert np.array_equal(X, RECORDED["relu"][1]["X"])
