import json
from pathlib import Path

import numpy as np
import pytest

from autograd import Tensor

MODELS = json.loads(Path("references/models.json").read_text())
RTOL, ATOL = 1e-10, 1e-12


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


def tensors(case, *names):
    return [Tensor(np.array(case[name])) for name in names]


@pytest.mark.id("tst_w0p08o")
def test_residual_network():
    """A network of residual blocks, each using its input twice, as PyTorch has it"""
    case = MODELS["residual"]
    (X,) = tensors(case, "X")
    layers = [tensors(layer, "weight", "bias") for layer in case["layers"]]
    x = X
    for weight, bias in layers:
        x = x + (x @ weight.T + bias).relu()
    out = x.mean()
    out.backward()
    assert out.data == pytest.approx(case["value"], rel=RTOL, abs=ATOL)
    assert close(X.grad, case["dX"])
    for (weight, bias), expected in zip(layers, case["gradients"], strict=True):
        assert close(weight.grad, expected["weight"])
        assert close(bias.grad, expected["bias"])


@pytest.mark.id("tst_oktdmb")
def test_weight_penalty():
    """A layer's loss with a weight penalty, each weight squared, as PyTorch has it"""
    case = MODELS["penalty"]
    X, weight, bias = tensors(case, "X", "weight", "bias")
    out = (X @ weight.T + bias).relu().mean() + (weight * weight).sum() * case["decay"]
    out.backward()
    assert out.data == pytest.approx(case["value"], rel=RTOL, abs=ATOL)
    assert close(X.grad, case["dX"])
    assert close(weight.grad, case["dweight"])
    assert close(bias.grad, case["dbias"])


@pytest.mark.id("tst_mqovhz")
def test_stable_log_sum_exp():
    """Each row's log-sum-exp with its largest logit taken out, as PyTorch has it"""
    case = MODELS["log_sum_exp"]
    (logits,) = tensors(case, "logits")
    largest = Tensor(logits.data.max(axis=1, keepdims=True))
    out = (logits - largest).exp().sum(axis=1).log().mean()
    out.backward()
    assert out.data == pytest.approx(case["value"], rel=RTOL, abs=ATOL)
    assert close(logits.grad, case["dlogits"])


@pytest.mark.id("tst_l7sbkj")
def test_tanh_layer():
    """A tanh layer's gradients, its inputs spread on either side of 0, as PyTorch has it"""
    case = MODELS["tanh"]
    X, weight, bias, dY = tensors(case, "X", "weight", "bias", "dY")
    Y = (X @ weight.T + bias).tanh()
    (Y * dY).sum().backward()
    assert close(Y.data, case["Y"])
    assert close(X.grad, case["dX"])
    assert close(weight.grad, case["dweight"])
    assert close(bias.grad, case["dbias"])
