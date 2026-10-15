import time

import numpy as np
import pytest

from gradients import gradient_agrees

SMALL, LARGE, LIMIT_S = 20, 200, 1.0


@pytest.fixture(scope="module")
def clinic():
    """The records, standardized, and their diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    X, y = table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]
    return (X - X.mean(axis=0)) / X.std(axis=0), y


def network(Z, y, hidden, seed=3, l2=0.0, scale=1.0, zero=False, mistake=None):
    """The network's loss and gradient over a flat array of its parameters, at random
    weights, with the gradient made wrong as mistake says."""
    d = Z.shape[1]
    size = d * hidden + 2 * hidden + 1
    theta = np.zeros(size) if zero else np.random.default_rng(seed).normal(0, 0.5, size)

    def split(t):
        return (
            t[: d * hidden].reshape(d, hidden),
            t[d * hidden : d * hidden + hidden],
            t[d * hidden + hidden : -1],
            t[-1],
        )

    def loss(t):
        W1, b1, w2, b2 = split(t)
        s = np.tanh(Z @ W1 + b1) @ w2 + b2
        decay = l2 / 2 * (np.sum(W1**2) + np.sum(w2**2))
        return scale * (float(np.mean(np.logaddexp(0, s) - y * s)) + decay)

    def gradient(t):
        W1, b1, w2, b2 = split(t)
        pre = Z @ W1 + b1
        hidden_out = np.tanh(pre)
        ds = (np.exp(-np.logaddexp(0, -(hidden_out @ w2 + b2))) - y) / len(y)
        slope = (1 - hidden_out) if mistake == "tanh" else (1 - hidden_out**2)
        dpre = np.outer(ds, w2) * slope
        dW1 = Z.T @ dpre + (0 if mistake == "decay" else l2 * W1)
        dw2 = (pre.T @ ds if mistake == "inputs" else hidden_out.T @ ds) + l2 * w2
        found = scale * np.concatenate([dW1.ravel(), dpre.sum(axis=0), dw2, [ds.sum()]])
        if mistake == "one weight":
            found[7] *= 1.01
        if mistake == "output bias":
            found[-1] *= -1
        return found

    return loss, gradient, theta


@pytest.mark.id("tst_hwdnqs")
def test_fast(clinic, record_property):
    """Fast on 6,401 parameters"""
    Z, y = clinic
    loss, gradient, theta = network(Z, y, SMALL)
    calls = 0

    def counted(t):
        nonlocal calls
        calls += 1
        return loss(t)

    gradient_agrees(counted, gradient, theta.copy(), np.random.default_rng(0))
    if calls > len(theta):
        record_property(
            "note",
            f"{calls:,} evaluations of the loss for {len(theta):,} parameters, so about "
            f"{calls * LARGE // SMALL:,} for {LARGE * Z.shape[1] + 2 * LARGE + 1:,}",
        )
        pytest.fail("It evaluates the loss more times than there are parameters.")
    loss, gradient, theta = network(Z, y, LARGE)
    start = time.perf_counter()
    gradient_agrees(loss, gradient, theta, np.random.default_rng(0))
    took = time.perf_counter() - start
    record_property("note", f"{took:.2f} seconds for {len(theta):,} parameters")
    assert took < LIMIT_S


@pytest.mark.id("tst_uimqfw")
def test_finds_mistakes(clinic):
    """Finds the assistant's mistakes"""
    Z, y = clinic
    for mistake, l2, scale in (
        ("tanh", 0.0, 1.0),
        ("decay", 0.1, 1.0),
        ("inputs", 0.0, 1.0),
        ("tanh", 0.0, 1e-6),
    ):
        loss, gradient, theta = network(Z, y, 4, l2=l2, scale=scale, mistake=mistake)
        assert not gradient_agrees(loss, gradient, theta, np.random.default_rng(4))


@pytest.mark.id("tst_kogsg6")
def test_finds_one_wrong_slope(clinic):
    """Finds one wrong slope among many"""
    Z, y = clinic
    for mistake in ("one weight", "output bias"):
        loss, gradient, theta = network(Z, y, 4, mistake=mistake)
        assert not gradient_agrees(loss, gradient, theta, np.random.default_rng(5))


@pytest.mark.id("tst_qkkinj")
def test_accepts_right_gradients(clinic):
    """Accepts a right gradient at any scale"""
    Z, y = clinic
    for options in ({}, {"scale": 1e-6}, {"scale": 1e6}, {"zero": True}):
        loss, gradient, theta = network(Z, y, 4, **options)
        assert gradient_agrees(loss, gradient, theta, np.random.default_rng(6))
