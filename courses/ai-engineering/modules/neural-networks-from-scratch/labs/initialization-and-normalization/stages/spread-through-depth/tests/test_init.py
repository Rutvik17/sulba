import json
import math
from pathlib import Path

import numpy as np
import pytest

from init import calculate_gain, kaiming_uniform, xavier_uniform

INIT = json.loads(Path("references/init.json").read_text())
STARTS = {"xavier_uniform": xavier_uniform, "kaiming_uniform": kaiming_uniform}


def largest(case):
    """The largest weight, in size, that your start draws for the case's shape."""
    start = STARTS[case["kind"]]
    weight = start(tuple(case["shape"]), np.random.default_rng(0), **case["settings"])
    assert weight.shape == tuple(case["shape"])
    return np.max(np.abs(weight))


@pytest.mark.id("tst_km53on")
def test_gains():
    """Each nonlinearity's gain, as torch.nn.init.calculate_gain gives it"""
    for case in INIT["gains"]:
        gain = calculate_gain(case["nonlinearity"], case["param"])
        assert gain == pytest.approx(case["gain"], rel=1e-12)


@pytest.mark.id("tst_lybyo9")
def test_unknown_nonlinearity():
    """A nonlinearity it has no gain for raises a ValueError"""
    with pytest.raises(ValueError):
        calculate_gain("softplus")


@pytest.mark.id("tst_oopmel")
def test_xavier():
    """Xavier's range for each recorded setting, as PyTorch draws it"""
    for case in INIT["starts"]:
        if case["kind"] == "xavier_uniform":
            assert largest(case) == pytest.approx(case["largest"], rel=1e-4)


@pytest.mark.id("tst_04bujh")
def test_kaiming():
    """Kaiming's range for each recorded setting, PyTorch's start for nn.Linear among
    them"""
    for case in INIT["starts"]:
        if case["kind"] == "kaiming_uniform":
            assert largest(case) == pytest.approx(case["largest"], rel=1e-4)


@pytest.mark.id("tst_5qqz4f")
def test_even_draws():
    """The weights fill their range evenly, drawn from rng"""
    first = kaiming_uniform((200, 300), np.random.default_rng(4), nonlinearity="relu")
    again = kaiming_uniform((200, 300), np.random.default_rng(4), nonlinearity="relu")
    assert np.array_equal(first, again)
    bound = math.sqrt(2) * math.sqrt(3 / 300)
    assert abs(np.mean(first)) < 0.01 * bound
    assert np.var(first) == pytest.approx(bound**2 / 3, rel=0.02)


@pytest.mark.id("tst_3gjrlm")
def test_fans():
    """A weight of shape (outputs, inputs) takes its range from its inputs, or from its
    outputs in fan_out mode"""
    wide = kaiming_uniform((10, 4000), np.random.default_rng(5), nonlinearity="relu")
    tall = kaiming_uniform(
        (4000, 10), np.random.default_rng(5), mode="fan_out", nonlinearity="relu"
    )
    assert np.max(np.abs(wide)) == pytest.approx(math.sqrt(6 / 4000), rel=1e-2)
    assert np.max(np.abs(tall)) == pytest.approx(math.sqrt(6 / 4000), rel=1e-2)
