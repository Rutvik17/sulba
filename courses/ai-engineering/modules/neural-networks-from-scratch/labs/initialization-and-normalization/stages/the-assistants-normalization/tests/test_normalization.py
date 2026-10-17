import numpy as np
import pytest

from normalization import BatchNorm1d, LayerNorm


@pytest.mark.id("tst_efebgw")
def test_training():
    """In training, each feature comes out with a mean of 0 and a variance of 1"""
    X = np.random.default_rng(0).normal(loc=3.0, scale=2.0, size=(16, 4))
    Y = BatchNorm1d(4).forward(X, training=True)
    assert np.allclose(Y.mean(axis=0), 0.0)
    assert np.allclose(Y.var(axis=0), 1.0, atol=1e-4)


@pytest.mark.id("tst_0uryk7")
def test_scale_and_shift():
    """The weight and the bias scale and shift each feature"""
    layer = BatchNorm1d(2)
    layer.weight[:] = [2.0, 3.0]
    layer.bias[:] = [1.0, -1.0]
    Y = layer.forward(np.array([[0.0, 1.0], [2.0, 5.0]]), training=True)
    assert np.allclose(Y, [[-1.0, -4.0], [3.0, 2.0]], atol=1e-4)


@pytest.mark.id("tst_48zeev")
def test_parameter_gradients():
    """The weight's and the bias's gradients, worked by hand"""
    layer = BatchNorm1d(1)
    layer.forward(np.array([[0.0], [2.0]]), training=True)
    layer.backward(np.array([[1.0], [3.0]]))
    # The batch normalizes to -1 and 1.
    assert layer.dweight == pytest.approx([2.0], rel=1e-4)
    assert layer.dbias == pytest.approx([4.0])


@pytest.mark.id("tst_ai1rsh")
def test_running_mean():
    """The running mean moves a tenth of the way to each batch's mean"""
    layer = BatchNorm1d(1)
    layer.forward(np.array([[4.0], [6.0]]), training=True)
    layer.forward(np.array([[4.0], [6.0]]), training=True)
    assert layer.running_mean == pytest.approx([0.5 + 0.45])


@pytest.mark.id("tst_kowbxf")
def test_layer_norm():
    """Layer normalization keeps its input's shape, and a constant input comes out as the
    bias"""
    layer = LayerNorm(3)
    layer.bias[:] = [1.0, 2.0, 3.0]
    Y = layer.forward(np.full((5, 3), 4.0))
    assert Y.shape == (5, 3)
    assert np.allclose(Y, [1.0, 2.0, 3.0])
