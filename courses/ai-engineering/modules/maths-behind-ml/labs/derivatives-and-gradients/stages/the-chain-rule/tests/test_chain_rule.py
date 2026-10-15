import numpy as np
import pytest

from gradients import network_gradient, network_loss

HIDDEN = 4


@pytest.fixture(scope="module")
def clinic():
    """The records, standardized, their diagnoses, and the network's weights at random."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    X, y = table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]
    rng = np.random.default_rng(0)
    d = X.shape[1]
    params = (
        rng.normal(0, 0.5, (d, HIDDEN)),
        rng.normal(0, 0.5, HIDDEN),
        rng.normal(0, 0.5, HIDDEN),
        float(rng.normal(0, 0.5)),
    )
    return (X - X.mean(axis=0)) / X.std(axis=0), y, params


def flat(parts):
    return np.concatenate([np.ravel(part) for part in parts])


def numerical(params, Z, y, h=1e-6):
    """Central differences of network_loss, one parameter at a time."""
    shapes = [np.shape(part) for part in params]
    theta = flat(params)

    def loss(t):
        parts, start = [], 0
        for shape in shapes:
            size = int(np.prod(shape))
            parts.append(t[start : start + size].reshape(shape))
            start += size
        parts[-1] = float(parts[-1])
        return network_loss(tuple(parts), Z, y)

    gradient = np.zeros(len(theta))
    for i in range(len(theta)):
        step = np.zeros(len(theta))
        step[i] = h
        gradient[i] = (loss(theta + step) - loss(theta - step)) / (2 * h)
    return gradient


def relative(a, b):
    return np.linalg.norm(a - b) / max(np.linalg.norm(a), np.linalg.norm(b))


@pytest.mark.id("tst_zuj9g0")
def test_loss(clinic):
    """The loss is log 2 untrained, right for one sample, and finite for a confident network"""
    Z, y, params = clinic
    zero = tuple(np.zeros_like(part) for part in params[:3]) + (0.0,)
    assert network_loss(zero, Z, y) == pytest.approx(np.log(2), rel=1e-12)
    one = (np.array([[0.5], [-0.25]]), np.array([0.0]), np.array([2.0]), 1.0)
    found = network_loss(one, np.array([[2.0, 0.0]]), np.array([1.0]))
    assert found == pytest.approx(
        np.log(1 + np.exp(-(2 * np.tanh(1.0) + 1))), rel=1e-12
    )
    W1, b1, w2, b2 = params
    confident = network_loss((W1, b1, 1000 * w2, 1000 * b2), Z, y)
    assert np.isfinite(confident) and confident > 1


@pytest.mark.id("tst_w6cvkv")
def test_shapes(clinic):
    """Each derivative has its parameter's shape"""
    Z, y, params = clinic
    found = network_gradient(params, Z, y)
    assert len(found) == 4
    for part, derivative in zip(params, found, strict=True):
        assert np.shape(derivative) == np.shape(part)


@pytest.mark.id("tst_6gt675")
def test_small_case():
    """One sample and one hidden unit, worked by hand"""
    params = (np.array([[0.5], [-0.25]]), np.array([0.0]), np.array([2.0]), 0.0)
    dW1, db1, dw2, db2 = network_gradient(
        params, np.array([[1.0, 2.0]]), np.array([1.0])
    )
    assert np.allclose(dW1, [[-1.0], [-2.0]], rtol=0, atol=1e-12)
    assert np.allclose(db1, [-1.0], rtol=0, atol=1e-12)
    assert np.allclose(dw2, [0.0], rtol=0, atol=1e-12)
    assert db2 == pytest.approx(-0.5, abs=1e-12)


@pytest.mark.id("tst_va4czh")
def test_matches_numerical(clinic):
    """The same as a numerical gradient, at random weights"""
    Z, y, params = clinic
    found = flat(network_gradient(params, Z, y))
    assert relative(found, numerical(params, Z, y)) < 1e-7


@pytest.mark.id("tst_j4c0q0")
def test_zero_weights_and_one_sample(clinic):
    """The same as a numerical gradient at zero weights, and for a single sample"""
    Z, y, params = clinic
    zero = tuple(np.zeros_like(part) for part in params[:3]) + (0.0,)
    assert relative(flat(network_gradient(zero, Z, y)), numerical(zero, Z, y)) < 1e-7
    one, label = Z[[17]], y[[17]]
    assert (
        relative(
            flat(network_gradient(params, one, label)), numerical(params, one, label)
        )
        < 1e-7
    )


@pytest.mark.id("tst_g9n2uv")
def test_inputs_kept(clinic):
    """The weights and data it's given stay as they were"""
    Z, y, params = clinic
    given = [part.copy() if isinstance(part, np.ndarray) else part for part in params]
    Z_given, y_given = Z.copy(), y.copy()
    network_gradient(tuple(given), Z_given, y_given)
    for kept, original in zip(given, params, strict=True):
        assert np.array_equal(kept, original)
    assert np.array_equal(Z_given, Z) and np.array_equal(y_given, y)
