import json
from pathlib import Path

import numpy as np
import pytest

from clipping import clip_grad_norm_, clip_grads_with_norm_, get_total_norm

CLIPPING = json.loads(Path("references/clipping.json").read_text())
# PyTorch's results and yours may differ in the last digits, from working in another order.
RTOL, ATOL = 1e-10, 1e-12


def arrays(case):
    return [np.array(grad) for grad in case["grads"]]


def close(found, expected):
    return all(
        np.allclose(f, e, rtol=RTOL, atol=ATOL) for f, e in zip(found, expected, strict=True)
    )


@pytest.mark.id("tst_lvngog")
def test_total_norms():
    """The total norm of gradients of several shapes, in each norm type, as PyTorch has it"""
    for case in CLIPPING["total_norms"]:
        norm_type = float(case["norm_type"])
        found = get_total_norm(arrays(case), norm_type)
        assert found == pytest.approx(case["total"], rel=RTOL)


@pytest.mark.id("tst_oed5vr")
def test_infinity():
    """In the infinity norm, the total is the largest size of any entry"""
    grads = [np.array([[1.0, -4.0], [2.0, 0.5]]), np.array([3.0, -1.0])]
    assert get_total_norm(grads, float("inf")) == 4.0
    assert get_total_norm(grads, 1.0) == pytest.approx(11.5)


@pytest.mark.id("tst_ddbbqp")
def test_clip_with_norm():
    """Gradients scaled for a total norm given to clip_grads_with_norm_, as PyTorch scales
    them"""
    for case in CLIPPING["clip_with_norm"]:
        grads = arrays(case)
        assert clip_grads_with_norm_(grads, case["max_norm"], case["total"]) is None
        assert close(grads, case["clipped"])


@pytest.mark.id("tst_qnboat")
def test_clip_norm():
    """clip_grad_norm_'s total norm and the gradients it leaves, as PyTorch has them"""
    for case in CLIPPING["clip_norm"]:
        grads = arrays(case)
        total = clip_grad_norm_(grads, case["max_norm"], float(case["norm_type"]))
        assert total == pytest.approx(case["total"], rel=RTOL, abs=ATOL)
        assert close(grads, case["clipped"])


@pytest.mark.id("tst_zetpm6")
def test_in_place():
    """The arrays given are the ones scaled"""
    grads = [np.full((2, 2), 3.0), np.full(2, 4.0)]
    held = list(grads)
    clip_grad_norm_(grads, 1.0)
    assert all(g is h for g, h in zip(grads, held, strict=True))
    assert np.all(held[0] < 3.0)


@pytest.mark.id("tst_0v0r63")
def test_together():
    """Clipped together, the gradients keep their direction, and their total norm comes
    down to the maximum"""
    grads = [np.array([[3.0, 0.0], [0.0, 4.0]]), np.array([12.0, 0.0])]
    before = [g.copy() for g in grads]
    assert clip_grad_norm_(grads, 1.0) == pytest.approx(13.0)
    assert get_total_norm(grads) == pytest.approx(1.0, rel=1e-6)
    assert grads[1][0] / grads[0][1][1] == pytest.approx(before[1][0] / before[0][1][1])


@pytest.mark.id("tst_cmviz7")
def test_below():
    """Gradients whose total norm is below the maximum are left as they were"""
    grads = [np.array([0.3, -0.4]), np.array([[0.0]])]
    clip_grad_norm_(grads, 1.0)
    assert np.array_equal(grads[0], [0.3, -0.4])
