import numpy as np
import pytest

from autograd import Tensor


@pytest.mark.id("tst_6vierf")
def test_add_and_multiply():
    """A sum of products, its value and gradients worked by hand"""
    a = Tensor(np.array([1.0, 2.0]))
    b = Tensor(np.array([3.0, 4.0]))
    c = Tensor(np.array([5.0, 6.0]))
    out = (a * b + c).sum()
    out.backward()
    assert out.data == 22.0
    assert np.array_equal(a.grad, [3.0, 4.0])
    assert np.array_equal(b.grad, [1.0, 2.0])
    assert np.array_equal(c.grad, [1.0, 1.0])


@pytest.mark.id("tst_e917fe")
def test_bias():
    """A bias added to every row gets the sum of the rows' gradients"""
    X = Tensor(np.ones((3, 2)))
    b = Tensor(np.array([0.5, -1.0]))
    (X + b).sum().backward()
    assert np.array_equal(X.grad, np.ones((3, 2)))
    assert np.array_equal(b.grad, [3.0, 3.0])


@pytest.mark.id("tst_r3ddga")
def test_matmul():
    """A matrix product's gradients, worked by hand"""
    A = Tensor(np.array([[1.0, 2.0], [3.0, 4.0]]))
    B = Tensor(np.array([[1.0], [-1.0]]))
    (A @ B).sum().backward()
    assert np.array_equal(A.grad, [[1.0, -1.0], [1.0, -1.0]])
    assert np.array_equal(B.grad, [[4.0], [6.0]])


@pytest.mark.id("tst_9bl9hl")
def test_sum_and_mean():
    """A sum along an axis, and a mean's gradient"""
    X = Tensor(np.arange(6.0).reshape(2, 3))
    assert np.array_equal(X.sum(axis=0).data, [3.0, 5.0, 7.0])
    X.mean().backward()
    assert np.allclose(X.grad, np.full((2, 3), 1 / 6))


@pytest.mark.id("tst_i5hrid")
def test_functions():
    """exp, log, tanh and relu at points worked by hand"""
    for name, x, value, slope in [
        ("exp", 0.0, 1.0, 1.0),
        ("log", 1.0, 0.0, 1.0),
        ("tanh", 0.0, 0.0, 1.0),
        ("relu", 2.0, 2.0, 1.0),
        ("relu", -2.0, 0.0, 0.0),
    ]:
        a = Tensor(np.array([x]))
        out = getattr(a, name)().sum()
        out.backward()
        assert out.data == value and a.grad[0] == slope
