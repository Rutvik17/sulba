import json
from pathlib import Path

import numpy as np
import pytest

from optimizers import Adam, AdamW

CASES = json.loads(Path("references/steps.json").read_text())["adamw"]
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


@pytest.mark.id("tst_bjkbm8")
def test_decay_alone():
    """With no gradient, each step shrinks every weight by the same share, the learning
    rate times the weight decay"""
    w = np.array([5.0, -0.2])
    optimizer = AdamW([w], lr=0.01, weight_decay=0.1)
    for _ in range(10):
        optimizer.step([np.zeros(2)])
    assert w == pytest.approx(np.array([5.0, -0.2]) * (1 - 0.01 * 0.1) ** 10, rel=1e-12)


@pytest.mark.id("tst_8ccgfn")
def test_same_share():
    """The decay takes the same share of every weight, however large its gradients"""
    start = np.array([1.0, 1.0])
    grads = [np.array([0.001, 1000.0]), np.array([0.002, -500.0])]
    decayed, plain = start.copy(), start.copy()
    with_decay = AdamW([decayed], lr=0.01, weight_decay=0.1)
    without = Adam([plain], lr=0.01)
    with_decay.step([grads[0]])
    without.step([grads[0]])
    assert plain - decayed == pytest.approx(0.01 * 0.1 * start, rel=1e-9)


@pytest.mark.id("tst_xss5gq")
def test_averages_without_decay():
    """The weight decay stays out of the averages of the gradient and its square"""
    w = np.array([3.0])
    optimizer = AdamW([w], lr=0.01, weight_decay=0.5)
    optimizer.step([np.array([2.0])])
    assert optimizer.m[0] == pytest.approx([0.1 * 2.0])
    assert optimizer.v[0] == pytest.approx([0.001 * 4.0])


@pytest.mark.id("tst_rf4sth")
def test_flag():
    """Adam with decoupled_weight_decay=True takes AdamW's steps, and AdamW's weight decay
    is 0.01 unless it's given"""
    rng = np.random.default_rng(2)
    a, b = rng.normal(size=3), np.zeros(3)
    b[:] = a
    first = Adam([a], lr=0.01, weight_decay=0.01, decoupled_weight_decay=True)
    second = AdamW([b], lr=0.01)
    for _ in range(5):
        grad = rng.normal(size=3)
        first.step([grad])
        second.step([grad])
    assert np.array_equal(a, b)
    assert second.weight_decay == 0.01


@pytest.mark.id("tst_loopw0")
def test_matches_pytorch():
    """The same steps as torch.optim.AdamW's, for each recorded case"""
    for case in CASES:
        for found, expected in zip(replay(AdamW, case), case["after"], strict=True):
            for param, want in zip(found, expected, strict=True):
                assert np.allclose(param, want, rtol=RTOL, atol=ATOL)
