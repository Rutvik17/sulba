import numpy as np
import pytest

from optim import SGD, Adam, AdamW


@pytest.mark.id("tst_nvi5dn")
def test_sgd_by_hand():
    """A step down the gradient, worked by hand"""
    optimizer = SGD([np.array([1.0, -2.0])], lr=0.5)
    optimizer.step([np.array([0.4, -1.0])])
    assert np.allclose(optimizer.params[0], [0.8, -1.5])


@pytest.mark.id("tst_0tsee5")
def test_momentum():
    """Momentum adds up the steps along a steady gradient"""
    optimizer = SGD([np.array([0.0])], lr=0.1, momentum=0.5)
    for _ in range(3):
        optimizer.step([np.array([1.0])])
    # Steps of 0.1, 0.15 and 0.175.
    assert np.allclose(optimizer.params[0], [-0.425])


@pytest.mark.id("tst_4rmwrs")
def test_adam_direction():
    """Adam moves each parameter against its gradient"""
    optimizer = Adam([np.zeros(3)], lr=0.01)
    optimizer.step([np.array([2.0, -0.5, 0.1])])
    assert np.array_equal(np.sign(optimizer.params[0]), [-1.0, 1.0, -1.0])


@pytest.mark.id("tst_smorz7")
def test_adam_scale():
    """Adam takes the same steps for gradients a thousand times as large"""
    small, large = Adam([np.zeros(2)], lr=0.01), Adam([np.zeros(2)], lr=0.01)
    for grad in [[1.0, -2.0], [0.5, -1.5], [2.0, 1.0], [-1.0, 0.5], [1.5, -0.5]]:
        small.step([np.array(grad)])
        large.step([1000 * np.array(grad)])
    assert np.allclose(small.params[0], large.params[0], rtol=1e-6)


@pytest.mark.id("tst_98hkxv")
def test_adamw_decays():
    """AdamW shrinks the weights when the loss's gradient is 0"""
    optimizer = AdamW([np.array([2.0, -3.0])], lr=0.01)
    for _ in range(5):
        optimizer.step([np.zeros(2)])
    assert np.all(np.abs(optimizer.params[0]) < [2.0, 3.0])
