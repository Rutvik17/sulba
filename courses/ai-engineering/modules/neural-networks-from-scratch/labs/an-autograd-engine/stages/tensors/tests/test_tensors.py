import json
from pathlib import Path

import numpy as np
import pytest

from engine import Tensor, unbroadcast

CASES = json.loads(Path("references/tensors.json").read_text())["cases"]
# PyTorch's results and yours may differ in the last digits, from summing in another order.
RTOL, ATOL = 1e-10, 1e-12


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


def evaluate(steps):
    """The last step's Tensor and the inputs' Tensors, from an expression written as steps,
    each an operation on the results of steps before it."""
    tensors, inputs = [], []
    for op, *args in steps:
        match op:
            case "input":
                tensor = Tensor(np.array(args[0]))
                inputs.append(tensor)
            case "add":
                tensor = tensors[args[0]] + tensors[args[1]]
            case "sub":
                tensor = tensors[args[0]] - tensors[args[1]]
            case "mul":
                tensor = tensors[args[0]] * tensors[args[1]]
            case "matmul":
                tensor = tensors[args[0]] @ tensors[args[1]]
            case "T":
                tensor = tensors[args[0]].T
            case "sum" | "mean":
                method = getattr(tensors[args[0]], op)
                tensor = method(axis=args[1], keepdims=args[2])
            case "neg":
                tensor = -tensors[args[0]]
            case _:
                tensor = getattr(tensors[args[0]], op)()
        tensors.append(tensor)
    return tensors[-1], inputs


@pytest.mark.id("tst_x88qjd")
def test_unbroadcast_by_hand():
    """A gradient summed back to each shape broadcasting can stretch to 4 by 3"""
    grad = np.arange(12.0).reshape(4, 3)
    assert np.array_equal(unbroadcast(grad, (4, 3)), grad)
    assert np.array_equal(unbroadcast(grad, (3,)), [18.0, 22.0, 26.0])
    assert np.array_equal(unbroadcast(grad, (1, 3)), [[18.0, 22.0, 26.0]])
    assert np.array_equal(unbroadcast(grad, (4, 1)), [[3.0], [12.0], [21.0], [30.0]])
    assert unbroadcast(grad, ()) == 66.0


@pytest.mark.id("tst_kj121u")
def test_bias_broadcast():
    """A bias added to every row gets the sum of the rows' gradients"""
    X, b = Tensor(np.ones((2, 3))), Tensor(np.array([1.0, 2.0, 3.0]))
    out = (X + b).sum()
    out.backward()
    assert out.data == 18.0
    assert np.array_equal(X.grad, np.ones((2, 3)))
    assert np.array_equal(b.grad, [2.0, 2.0, 2.0])


@pytest.mark.id("tst_esf2q1")
def test_matmul_by_hand():
    """A matrix product's gradients, worked by hand"""
    A = Tensor(np.array([[1.0, 2.0], [3.0, 4.0]]))
    B = Tensor(np.array([[5.0], [6.0]]))
    (A @ B).sum().backward()
    assert np.array_equal(A.grad, [[5.0, 6.0], [5.0, 6.0]])
    assert np.array_equal(B.grad, [[4.0], [6.0]])


@pytest.mark.id("tst_y4wsd7")
def test_sums_and_means():
    """Sums and means along an axis, with and without its length kept"""
    X = Tensor(np.arange(6.0).reshape(2, 3))
    assert X.sum(axis=1).data.shape == (2,)
    assert X.sum(axis=0, keepdims=True).data.shape == (1, 3)
    out = (X.sum(axis=1) * Tensor(np.array([1.0, 2.0]))).sum() + X.mean()
    out.backward()
    assert np.allclose(X.grad, [[1 + 1 / 6] * 3, [2 + 1 / 6] * 3], rtol=0, atol=1e-15)


@pytest.mark.id("tst_qk3opi")
def test_used_twice():
    """A tensor used twice gets a gradient from each use"""
    X = Tensor(np.array([[1.0, -2.0], [0.5, 3.0]]))
    (X * X).sum().backward()
    assert np.array_equal(X.grad, 2 * X.data)


@pytest.mark.id("tst_trbpuy")
def test_matches_pytorch():
    """The same value and gradients as PyTorch's, for each recorded expression"""
    for case in CASES:
        out, inputs = evaluate(case["steps"])
        out.backward()
        assert out.data == pytest.approx(case["value"], rel=RTOL, abs=ATOL)
        for tensor, expected in zip(inputs, case["gradients"], strict=True):
            assert tensor.grad.shape == tensor.data.shape
            assert close(tensor.grad, expected)
