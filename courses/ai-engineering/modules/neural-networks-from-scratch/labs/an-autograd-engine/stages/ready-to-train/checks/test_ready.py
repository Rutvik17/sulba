import json
from pathlib import Path

import numpy as np
import pytest

from engine import Tensor, Value, cross_entropy

DEPTH, STEP = 10_000, 1e-4
CONFIDENT = json.loads(Path("references/models.json").read_text())["cross_entropy"][-1]


@pytest.mark.id("tst_38eu62")
def test_deep_graphs(record_property):
    """Graphs 10,000 steps deep"""
    # Each step uses the one before twice, x + x * STEP, so the gradient is (1 + STEP)
    # to the power of DEPTH.
    try:
        a = Value(1.0)
        value = a
        for _ in range(DEPTH):
            value = value + value * STEP
        value.backward()
        x = Tensor(np.ones(3))
        tensor = x
        for _ in range(DEPTH):
            tensor = tensor + tensor * STEP
        tensor.sum().backward()
    except RecursionError:
        record_property("note", "RecursionError")
        raise
    assert a.grad == pytest.approx((1 + STEP) ** DEPTH, rel=1e-9)
    assert np.allclose(x.grad, (1 + STEP) ** DEPTH, rtol=1e-9, atol=0)


@pytest.mark.id("tst_d95r9h")
def test_confident_logits(record_property):
    """Confident logits"""
    logits = Tensor(np.array(CONFIDENT["logits"]))
    with np.errstate(all="ignore"):
        loss = cross_entropy(logits, np.array(CONFIDENT["labels"]))
        loss.backward()
    record_property("note", f"loss {float(loss.data):,.1f}")
    assert loss.data == pytest.approx(CONFIDENT["loss"], rel=1e-10, abs=1e-12)
    assert np.all(np.isfinite(logits.grad))
    assert np.allclose(logits.grad, CONFIDENT["dlogits"], rtol=1e-10, atol=1e-12)
