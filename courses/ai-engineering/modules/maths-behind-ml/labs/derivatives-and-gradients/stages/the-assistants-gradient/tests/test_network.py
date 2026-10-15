import numpy as np
import pytest

from network import gradient, loss

HIDDEN, L2 = 4, 0.01


@pytest.fixture(scope="module")
def clinic():
    """The records, standardized, and their diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    X, y = table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]
    return (X - X.mean(axis=0)) / X.std(axis=0), y


def untrained(d):
    """The network before training: every weight and bias 0."""
    return (np.zeros((d, HIDDEN)), np.zeros(HIDDEN), np.zeros(HIDDEN), 0.0)


def flat(parts):
    return np.concatenate([np.ravel(part) for part in parts])


def unflat(theta, d):
    return (
        theta[: d * HIDDEN].reshape(d, HIDDEN),
        theta[d * HIDDEN : d * HIDDEN + HIDDEN],
        theta[d * HIDDEN + HIDDEN : d * HIDDEN + 2 * HIDDEN],
        float(theta[-1]),
    )


@pytest.mark.id("tst_148nnh")
def test_shapes(clinic):
    """Each derivative has its parameter's shape"""
    Z, y = clinic
    params = untrained(Z.shape[1])
    for part, derivative in zip(params, gradient(params, Z, y, L2), strict=True):
        assert np.shape(derivative) == np.shape(part)


@pytest.mark.id("tst_mv8p1u")
def test_untrained_loss(clinic):
    """Untrained, the loss is log 2"""
    Z, y = clinic
    assert loss(untrained(Z.shape[1]), Z, y, L2) == pytest.approx(np.log(2), rel=1e-12)


@pytest.mark.id("tst_3vh7dx")
def test_numerical(clinic):
    """The gradient matches a numerical one, weight decay included"""
    Z, y = clinic
    d = Z.shape[1]
    theta = flat(untrained(d))
    numerical = np.zeros(len(theta))
    for i in range(len(theta)):
        step = np.zeros(len(theta))
        step[i] = 1e-6
        up, down = (
            loss(unflat(theta + step, d), Z, y, L2),
            loss(unflat(theta - step, d), Z, y, L2),
        )
        numerical[i] = (up - down) / 2e-6
    found = flat(gradient(unflat(theta, d), Z, y, L2))
    assert np.linalg.norm(found - numerical) / np.linalg.norm(found) < 1e-6


@pytest.mark.id("tst_dcdrdd")
def test_step_lowers_loss(clinic):
    """A step down the gradient lowers the loss"""
    Z, y = clinic
    d = Z.shape[1]
    params = untrained(d)
    stepped = unflat(flat(params) - 0.5 * flat(gradient(params, Z, y, L2)), d)
    assert loss(stepped, Z, y, L2) < loss(params, Z, y, L2)
