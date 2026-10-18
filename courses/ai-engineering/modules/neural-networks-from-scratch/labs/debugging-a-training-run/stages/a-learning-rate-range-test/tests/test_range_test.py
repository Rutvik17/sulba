import numpy as np
import pytest

from network import network
from range_test import lowest, range_test


def scripted(losses, seen=None):
    """A loss_and_grads that gives the scripted losses in turn and a gradient of 1, and
    notes the parameter each step sees."""
    script = iter(losses)

    def loss_and_grads(params, X, digits):
        if seen is not None:
            seen.append(params[0].copy())
        return next(script), [np.ones_like(params[0])]

    return loss_and_grads


def batches(count):
    return [(None, None)] * count


@pytest.mark.id("tst_xgss4a")
def test_rates():
    """The learning rates rise geometrically, one for each batch"""
    lrs, _ = range_test(
        [np.zeros(1)], batches(5), 1e-3, 10.0, loss_and_grads=scripted([1.0] * 5)
    )
    assert np.allclose(lrs, [1e-3, 1e-2, 1e-1, 1.0, 10.0])


@pytest.mark.id("tst_y00bgq")
def test_smoothing():
    """The smoothed loss, worked by hand: an average from 0, divided by 1 - beta^t"""
    script = scripted([4.0, 2.0, 2.0, 1.0])
    _, smoothed = range_test(
        [np.zeros(1)], batches(4), 0.1, 1.0, beta=0.5, loss_and_grads=script
    )
    assert np.allclose(smoothed, [4.0, 2.0 / 0.75, 2.0 / 0.875, 1.5 / 0.9375])


@pytest.mark.id("tst_dem1ow")
def test_stop():
    """It stops at the step whose smoothed loss passes stop times its lowest"""
    script = scripted([1.0, 1.0, 1.0, 30.0, 300.0, 3000.0])
    lrs, smoothed = range_test(
        [np.zeros(1)], batches(6), 0.1, 1.0, beta=0.5, loss_and_grads=script
    )
    # The fourth step's smoothed loss, 15.4375 / 0.9375, is the first past 4 times the
    # lowest, 1.
    assert len(smoothed) == len(lrs) == 4
    assert smoothed[-1] == pytest.approx(15.4375 / 0.9375)


@pytest.mark.id("tst_7i5upk")
def test_steps():
    """Each step moves the network by that step's learning rate times the gradient"""
    seen = []
    lrs, _ = range_test(
        [np.zeros(1)], batches(4), 0.5, 4.0, loss_and_grads=scripted([1.0] * 4, seen)
    )
    expected = -np.concatenate([[0.0], np.cumsum(lrs[:-1])])
    assert np.allclose([s[0] for s in seen], expected)


@pytest.mark.id("tst_9qtmws")
def test_copy():
    """The range test leaves the network as it was"""
    params = [np.zeros(3)]
    range_test(params, batches(3), 0.1, 1.0, loss_and_grads=scripted([1.0] * 3))
    assert np.array_equal(params[0], np.zeros(3))


@pytest.mark.id("tst_mdatdy")
def test_not_finite():
    """It stops at a loss that isn't a number"""
    script = scripted([1.0, float("nan"), 1.0])
    lrs, smoothed = range_test(
        [np.zeros(1)], batches(3), 0.1, 1.0, loss_and_grads=script
    )
    assert len(lrs) == 2 and np.isnan(smoothed[-1])


@pytest.mark.id("tst_l9jwzr")
def test_lowest():
    """The learning rate at the lowest smoothed loss"""
    assert lowest(np.array([0.1, 1.0, 10.0]), np.array([2.0, 1.5, 3.0])) == 1.0


@pytest.mark.id("tst_ex087r")
def test_office():
    """On the office's network, the smoothed loss falls, then rises"""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    training = table[table[:, 0] == 0]
    rng = np.random.default_rng(3)
    rows = [rng.choice(len(training), size=64, replace=False) for _ in range(300)]
    data = [(training[r, 2:] / 16, training[r, 1].astype(np.int64)) for r in rows]
    lrs, smoothed = range_test(network(np.random.default_rng(3)), data, 1e-3, 10.0)
    at = int(np.argmin(smoothed))
    assert smoothed[at] < smoothed[0] - 0.2
    assert smoothed[-1] > smoothed[at] + 0.2
    assert 0.1 < lrs[at] < 10
