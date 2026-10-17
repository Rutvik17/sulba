import json
from pathlib import Path

import numpy as np
import pytest

from optimizers import SGD

CASES = json.loads(Path("references/steps.json").read_text())["sgd"]
# PyTorch's results and yours may differ in the last digits, from working in another order.
RTOL, ATOL = 1e-10, 1e-12


def replay(make, case):
    """The parameters after each of a recorded case's steps, taken by an optimizer that
    make gives."""
    params = [np.array(p) for p in case["params"]]
    optimizer = make(params, **case["settings"])
    found = []
    for number, grads in enumerate(case["grads"]):
        if case["lrs"]:
            optimizer.lr = case["lrs"][number]
        optimizer.step([np.array(g) for g in grads])
        found.append([p.copy() for p in params])
    return found


@pytest.mark.id("tst_r4iits")
def test_by_hand():
    """A step down the gradient, worked by hand"""
    w = np.array([1.0, -2.0])
    SGD([w], lr=0.5).step([np.array([0.4, -1.0])])
    assert np.array_equal(w, [0.8, -1.5])


@pytest.mark.id("tst_a56jk2")
def test_momentum_by_hand():
    """Momentum's first step is the gradient's, and each later one adds the gradient to
    the velocity"""
    w = np.array([0.0])
    optimizer = SGD([w], lr=0.1, momentum=0.5)
    optimizer.step([np.array([2.0])])
    assert w == pytest.approx([-0.2])
    optimizer.step([np.array([2.0])])
    assert w == pytest.approx([-0.5])


@pytest.mark.id("tst_jxivm1")
def test_dampening():
    """Dampening scales the gradient from the second step on, not at the first"""
    w = np.array([0.0])
    optimizer = SGD([w], lr=1.0, momentum=0.5, dampening=0.5)
    optimizer.step([np.array([2.0])])
    assert w == pytest.approx([-2.0])
    optimizer.step([np.array([2.0])])
    assert w == pytest.approx([-4.0])


@pytest.mark.id("tst_nkc60i")
def test_weight_decay_and_nesterov():
    """Weight decay and Nesterov's momentum, worked by hand"""
    w = np.array([2.0])
    SGD([w], lr=0.5, weight_decay=0.1).step([np.array([1.0])])
    assert w == pytest.approx([1.4])
    v = np.array([0.0])
    SGD([v], lr=0.1, momentum=0.5, nesterov=True).step([np.array([1.0])])
    assert v == pytest.approx([-0.15])


@pytest.mark.id("tst_suakvh")
def test_in_place():
    """Each step changes the arrays it was given, which the network holds, and leaves the
    gradients as they were"""
    weight, bias = np.ones((2, 3)), np.zeros(3)
    optimizer = SGD([weight, bias], lr=0.1, momentum=0.9)
    for _ in range(2):
        grads = [np.ones((2, 3)), np.ones(3)]
        optimizer.step(grads)
        assert np.array_equal(grads[0], np.ones((2, 3)))
        assert np.array_equal(grads[1], np.ones(3))
    assert optimizer.params[0] is weight and optimizer.params[1] is bias
    assert np.allclose(weight, 1 - 0.1 - 0.19) and np.allclose(bias, -0.1 - 0.19)


@pytest.mark.id("tst_n7um0z")
def test_new_learning_rate():
    """A new learning rate takes effect at once, on the whole step, momentum and all"""
    w = np.array([0.0])
    optimizer = SGD([w], lr=1.0, momentum=0.5)
    optimizer.step([np.array([1.0])])
    optimizer.lr = 0.1
    optimizer.step([np.array([1.0])])
    assert w == pytest.approx([-1.15])


@pytest.mark.id("tst_kb9e2u")
def test_matches_pytorch():
    """The same steps as torch.optim.SGD's, for each recorded case"""
    for case in CASES:
        for found, expected in zip(replay(SGD, case), case["after"], strict=True):
            for param, want in zip(found, expected, strict=True):
                assert np.allclose(param, want, rtol=RTOL, atol=ATOL)
