import json
from pathlib import Path

import numpy as np
import pytest

from optimizers import Adam

CASES = json.loads(Path("references/steps.json").read_text())["adam"]
# PyTorch's results and yours may differ in the last digits, from working in another order.
RTOL, ATOL = 1e-10, 1e-12


def replay(make, case):
    """The parameters after each of a recorded case's steps, taken by an optimizer that
    make gives."""
    params = [np.array(p) for p in case["params"]]
    optimizer = make(params, **case["settings"])
    found = []
    for grads in case["grads"]:
        optimizer.step([np.array(g) for g in grads])
        found.append([p.copy() for p in params])
    return found


@pytest.mark.id("tst_zd0jlf")
def test_first_step():
    """The first step moves each parameter by the learning rate, against its gradient,
    whatever the gradient's size"""
    w = np.ones(3)
    Adam([w], lr=0.1).step([np.array([0.5, -2.0, 0.01])])
    assert w == pytest.approx([0.9, 1.1, 0.9], rel=1e-6)


@pytest.mark.id("tst_5gc3z4")
def test_by_hand():
    """Two steps, the averages starting at 0 and corrected by 1 - β to the power t"""
    w = np.array([0.0])
    optimizer = Adam([w], lr=1.0, betas=(0.5, 0.5))
    optimizer.step([np.array([1.0])])
    optimizer.step([np.array([3.0])])
    # After the second step the averages are 1.75 and 4.75, each over 1 - 0.5 ** 2.
    second = (1.75 / 0.75) / (np.sqrt(4.75 / 0.75) + 1e-8)
    assert w == pytest.approx([-1 / (1 + 1e-8) - second])
    assert optimizer.t == 2


@pytest.mark.id("tst_ah36fu")
def test_scale():
    """Gradients a thousand times as large take the same steps"""
    small, large = np.zeros(2), np.zeros(2)
    first, second = Adam([small], lr=0.01), Adam([large], lr=0.01)
    rng = np.random.default_rng(1)
    for _ in range(5):
        grad = rng.normal(size=2)
        first.step([grad])
        second.step([1000 * grad])
    assert large == pytest.approx(small, rel=1e-6)


@pytest.mark.id("tst_2b8k6c")
def test_weight_decay():
    """Weight decay added to the gradient: with no gradient, each weight moves by the
    learning rate toward 0, whatever its size"""
    w = np.array([5.0, -0.2])
    Adam([w], lr=0.01, weight_decay=0.1).step([np.zeros(2)])
    assert w == pytest.approx([4.99, -0.19], rel=1e-6)


@pytest.mark.id("tst_3ehso3")
def test_in_place():
    """Each step changes the arrays it was given, and leaves the gradients as they were"""
    weight, bias = np.ones((2, 3)), np.zeros(3)
    optimizer = Adam([weight, bias], lr=0.1)
    grads = [np.ones((2, 3)), np.ones(3)]
    optimizer.step(grads)
    assert optimizer.params[0] is weight and optimizer.params[1] is bias
    assert np.array_equal(grads[0], np.ones((2, 3))) and np.array_equal(
        grads[1], np.ones(3)
    )
    assert np.allclose(weight, 0.9) and np.allclose(bias, -0.1)


@pytest.mark.id("tst_q5ljh4")
def test_matches_pytorch():
    """The same steps as torch.optim.Adam's, for each recorded case"""
    for case in CASES:
        for found, expected in zip(replay(Adam, case), case["after"], strict=True):
            for param, want in zip(found, expected, strict=True):
                assert np.allclose(param, want, rtol=RTOL, atol=ATOL)
