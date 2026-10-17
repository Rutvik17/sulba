import json
from pathlib import Path

import numpy as np
import pytest

from network import Linear, Network, ReLU, cross_entropy

ACTIVATIONS = json.loads(Path("references/activations.json").read_text())
NETWORKS = json.loads(Path("references/networks.json").read_text())["networks"]
LINEAR = json.loads(Path("references/linear.json").read_text())["cases"]
RTOL, ATOL = 1e-10, 1e-12


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


def softmax_gradient(logits, labels):
    """The mean cross-entropy's gradient, worked out here so the check tests the layers."""
    shifted = logits - logits.max(axis=1, keepdims=True)
    gradient = np.exp(shifted) / np.exp(shifted).sum(axis=1, keepdims=True)
    gradient[np.arange(len(labels)), labels] -= 1
    return gradient / len(labels)


@pytest.mark.id("tst_71yzcs")
def test_gradient_for_a_batch():
    """The loss's gradient for batches of digits, as PyTorch gives it"""
    for case in ACTIVATIONS["cross_entropy"][1:3]:
        _, dlogits = cross_entropy(np.array(case["logits"]), np.array(case["labels"]))
        assert close(dlogits, case["dlogits"])


@pytest.mark.id("tst_sfw6xb")
def test_confident_logits():
    """A finite loss and gradient for logits in the thousands"""
    case = ACTIVATIONS["cross_entropy"][3]
    loss, dlogits = cross_entropy(np.array(case["logits"]), np.array(case["labels"]))
    assert loss == pytest.approx(case["loss"], rel=RTOL, abs=ATOL)
    assert np.all(np.isfinite(dlogits))


@pytest.mark.id("tst_vave1o")
def test_networks_of_more_layers():
    """Every gradient of networks with one hidden layer and with two"""
    for case in NETWORKS:
        layers = []
        for number, layer in enumerate(case["layers"]):
            if number:
                layers.append(ReLU())
            layers.append(Linear(np.array(layer["weight"]), np.array(layer["bias"])))
        network = Network(layers)
        logits = network.forward(np.array(case["X"]))
        network.backward(softmax_gradient(logits, np.array(case["labels"])))
        linears = [layer for layer in layers if isinstance(layer, Linear)]
        for layer, expected in zip(linears, case["gradients"], strict=True):
            assert close(layer.dweight, expected["weight"])
            assert close(layer.dbias, expected["bias"])


@pytest.mark.id("tst_e8uepi")
def test_gradients_step_after_step():
    """After a second backward pass, a layer holds that pass's gradients"""
    case = LINEAR[1]
    layer = Linear(np.array(case["weight"]), np.array(case["bias"]))
    X, dY = np.array(case["X"]), np.array(case["dY"])
    layer.forward(X)
    layer.backward(dY)
    layer.forward(X[::-1])
    layer.backward(2 * dY)
    assert close(layer.dweight, (2 * dY).T @ X[::-1])
    assert close(layer.dbias, (2 * dY).sum(axis=0))
