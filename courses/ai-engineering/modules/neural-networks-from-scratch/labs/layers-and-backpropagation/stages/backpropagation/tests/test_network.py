import json
from pathlib import Path

import numpy as np
import pytest

from layers import Linear, Network, ReLU, cross_entropy, linear_layer

NETWORKS = json.loads(Path("references/networks.json").read_text())["networks"]
# PyTorch's results and yours may differ in the last digits, from summing in another order.
RTOL, ATOL = 1e-10, 1e-12


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


def recorded(case):
    """A recorded network: its linear layers, with a ReLU between each two."""
    layers = []
    for number, layer in enumerate(case["layers"]):
        if number:
            layers.append(ReLU())
        layers.append(Linear(np.array(layer["weight"]), np.array(layer["bias"])))
    return Network(layers)


@pytest.mark.id("tst_1p46ee")
def test_logits_and_loss_match_pytorch():
    """The same logits and loss as PyTorch's, for both recorded networks"""
    for case in NETWORKS:
        logits = recorded(case).forward(np.array(case["X"]))
        assert close(logits, case["logits"])
        loss, _ = cross_entropy(logits, np.array(case["labels"]))
        assert loss == pytest.approx(case["loss"], rel=RTOL, abs=ATOL)


@pytest.mark.id("tst_w9ur1l")
def test_gradients_match_pytorch():
    """Every gradient the same as PyTorch's, with one hidden layer and with two"""
    for case in NETWORKS:
        network = recorded(case)
        logits = network.forward(np.array(case["X"]))
        _, dlogits = cross_entropy(logits, np.array(case["labels"]))
        assert close(network.backward(dlogits), case["dX"])
        linears = [layer for layer in network.layers if isinstance(layer, Linear)]
        for layer, expected in zip(linears, case["gradients"], strict=True):
            assert close(layer.dweight, expected["weight"])
            assert close(layer.dbias, expected["bias"])


@pytest.mark.id("tst_bchlt0")
def test_step_by_hand():
    """A step moves each weight and bias down its gradient, worked by hand"""
    first = Linear(np.array([[1.0, 2.0]]), np.array([0.5]))
    second = Linear(np.array([[3.0]]), np.array([0.0]))
    network = Network([first, ReLU(), second])
    network.forward(np.array([[1.0, 1.0]]))
    network.backward(np.array([[2.0]]))
    network.step(0.1)
    assert np.allclose(first.weight, [[0.4, 1.4]], rtol=0, atol=1e-12)
    assert np.allclose(first.bias, [-0.1], rtol=0, atol=1e-12)
    assert np.allclose(second.weight, [[2.3]], rtol=0, atol=1e-12)
    assert np.allclose(second.bias, [-0.2], rtol=0, atol=1e-12)


@pytest.mark.id("tst_49tkkr")
def test_steps_lower_the_loss():
    """Steps down the gradient lower a batch's loss"""
    case = NETWORKS[0]
    network = recorded(case)
    X, labels = np.array(case["X"]), np.array(case["labels"])
    losses = []
    for _ in range(10):
        loss, dlogits = cross_entropy(network.forward(X), labels)
        losses.append(loss)
        network.backward(dlogits)
        network.step(0.1)
    assert all(later < earlier for earlier, later in zip(losses, losses[1:]))


@pytest.mark.id("tst_aphqoq")
def test_linear_layer_starts_as_pytorch():
    """A new layer's shapes, and weights and biases spread as PyTorch's nn.Linear spreads them"""
    layer = linear_layer(64, 16, np.random.default_rng(0))
    assert layer.weight.shape == (16, 64) and layer.bias.shape == (16,)
    bound = 1 / np.sqrt(64)
    assert np.all(np.abs(layer.weight) <= bound) and np.all(np.abs(layer.bias) <= bound)
    # A uniform spread from -bound to bound has a standard deviation of bound / sqrt(3).
    assert np.std(layer.weight) == pytest.approx(bound / np.sqrt(3), rel=0.1)


@pytest.mark.id("tst_39x2gi")
def test_linear_layer_uses_rng():
    """The same seed gives the same layer, and another seed another"""
    same = [linear_layer(8, 4, np.random.default_rng(1)) for _ in range(2)]
    assert np.array_equal(same[0].weight, same[1].weight)
    assert np.array_equal(same[0].bias, same[1].bias)
    other = linear_layer(8, 4, np.random.default_rng(2))
    assert not np.array_equal(same[0].weight, other.weight)
