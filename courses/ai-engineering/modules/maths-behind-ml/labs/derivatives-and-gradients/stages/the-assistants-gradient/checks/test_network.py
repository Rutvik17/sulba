import numpy as np
import pytest

from network import gradient, loss

HIDDEN, L2 = 4, 0.1


@pytest.fixture(scope="module")
def clinic():
    """The records, standardized, their diagnoses, and the network's weights partway
    through training: at random."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    X, y = table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]
    rng = np.random.default_rng(1)
    d = X.shape[1]
    params = (
        rng.normal(0, 0.5, (d, HIDDEN)),
        rng.normal(0, 0.5, HIDDEN),
        rng.normal(0, 0.5, HIDDEN),
        float(rng.normal(0, 0.5)),
    )
    return (X - X.mean(axis=0)) / X.std(axis=0), y, params


def expected_loss(params, Z, y, l2=0.0):
    W1, b1, w2, b2 = params
    s = np.tanh(Z @ W1 + b1) @ w2 + b2
    return float(
        np.mean(np.logaddexp(0, s) - y * s) + l2 / 2 * (np.sum(W1**2) + np.sum(w2**2))
    )


def expected_gradient(params, Z, y, l2=0.0):
    W1, b1, w2, b2 = params
    hidden = np.tanh(Z @ W1 + b1)
    ds = (np.exp(-np.logaddexp(0, -(hidden @ w2 + b2))) - y) / len(y)
    dpre = np.outer(ds, w2) * (1 - hidden**2)
    return (
        Z.T @ dpre + l2 * W1,
        dpre.sum(axis=0),
        hidden.T @ ds + l2 * w2,
        float(ds.sum()),
    )


def relative(found, expected):
    a = np.concatenate([np.ravel(np.asarray(part, dtype=float)) for part in found])
    b = np.concatenate([np.ravel(part) for part in expected])
    return np.linalg.norm(a - b) / np.linalg.norm(b)


@pytest.mark.id("tst_xjwwpv")
def test_hidden_layer(clinic):
    """The hidden layer's gradient at random weights"""
    Z, y, params = clinic
    found = gradient(params, Z.copy(), y.copy())
    assert relative(found[:2], expected_gradient(params, Z, y)[:2]) < 1e-9


@pytest.mark.id("tst_8msk9r")
def test_decay_on_hidden_layer(clinic):
    """Weight decay on the hidden layer's weights"""
    Z, y, params = clinic
    without = np.asarray(gradient(params, Z.copy(), y.copy(), 0.0)[0], dtype=float)
    decayed = np.asarray(gradient(params, Z.copy(), y.copy(), L2)[0], dtype=float)
    assert np.allclose(decayed - without, L2 * params[0], rtol=1e-6, atol=1e-12)


@pytest.mark.id("tst_pop4e7")
def test_output_weights(clinic):
    """The output weights' gradient at random weights"""
    Z, y, params = clinic
    found = gradient(params, Z.copy(), y.copy())
    assert relative(found[2:3], expected_gradient(params, Z, y)[2:3]) < 1e-9


@pytest.mark.id("tst_8x0phj")
def test_confident_network(clinic):
    """A finite loss for a confident network"""
    Z, y, params = clinic
    W1, b1, w2, b2 = params
    confident = (W1, b1, w2 * 1000, b2 * 1000)
    found = loss(confident, Z.copy(), y.copy())
    assert np.isfinite(found)
    assert found == pytest.approx(expected_loss(confident, Z, y), rel=1e-9)
