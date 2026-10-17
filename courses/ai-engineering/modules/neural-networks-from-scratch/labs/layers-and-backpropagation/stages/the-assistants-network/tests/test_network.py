import numpy as np
import pytest

from network import Linear, Network, ReLU, cross_entropy


@pytest.mark.id("tst_8sp836")
def test_linear_by_hand():
    """A linear layer's outputs and gradients for one sample"""
    layer = Linear(np.array([[1.0, 2.0], [0.5, -1.0]]), np.array([0.25, 1.0]))
    assert np.allclose(layer.forward(np.array([[3.0, -1.0]])), [[1.25, 3.5]])
    assert np.allclose(layer.backward(np.array([[1.0, -2.0]])), [[0.0, 4.0]])
    assert np.allclose(layer.dweight, [[3.0, -1.0], [-6.0, 2.0]])
    assert np.allclose(layer.dbias, [1.0, -2.0])


@pytest.mark.id("tst_8d9x4j")
def test_relu_by_hand():
    """ReLU's outputs and gradient below 0, at 0 and above 0"""
    relu = ReLU()
    assert np.array_equal(relu.forward(np.array([[-2.0, 0.0, 3.0]])), [[0.0, 0.0, 3.0]])
    assert np.array_equal(relu.backward(np.array([[5.0, 6.0, 7.0]])), [[0.0, 0.0, 7.0]])


@pytest.mark.id("tst_4f22hd")
def test_cross_entropy_by_hand():
    """The loss and gradient for one digit, worked by hand"""
    logits = np.array([[0.0, np.log(3.0)]])
    loss, dlogits = cross_entropy(logits, np.array([1]))
    assert loss == pytest.approx(np.log(4 / 3))
    assert np.allclose(dlogits, [[0.25, -0.25]])


@pytest.mark.id("tst_dg29aq")
def test_network_by_hand():
    """A network of one linear layer gives the layer's outputs and gradients"""
    network = Network([Linear(np.array([[2.0, -1.0]]), np.array([0.5]))])
    assert np.allclose(network.forward(np.array([[1.0, 3.0]])), [[-0.5]])
    assert np.allclose(network.backward(np.array([[2.0]])), [[4.0, -2.0]])
    assert np.allclose(network.layers[0].dweight, [[2.0, 6.0]])


@pytest.mark.id("tst_dtyehz")
def test_step_by_hand():
    """A step moves the weight and bias down their gradients"""
    layer = Linear(np.array([[2.0, -1.0]]), np.array([0.5]))
    network = Network([layer])
    network.forward(np.array([[1.0, 3.0]]))
    network.backward(np.array([[2.0]]))
    network.step(0.5)
    assert np.allclose(layer.weight, [[1.0, -4.0]])
    assert np.allclose(layer.bias, [-0.5])
