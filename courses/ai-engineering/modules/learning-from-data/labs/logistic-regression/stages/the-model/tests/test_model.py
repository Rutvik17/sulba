import warnings

import numpy as np
import pytest

from model import predict_proba, sigmoid


def training_features():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    return table[table[:, 0] == 0, 2:]


def expected_sigmoid(z):
    """The sigmoid by NumPy's logaddexp, a form that never overflows."""
    return np.exp(-np.logaddexp(0.0, -np.asarray(z, dtype=float)))


@pytest.mark.id("tst_fvhv3i")
def test_half_at_zero():
    """Half at zero"""
    assert sigmoid(0.0) == pytest.approx(0.5)


@pytest.mark.id("tst_cjvrji")
def test_on_an_array():
    """On an array"""
    z = np.array([-2.0, 0.0, 2.0])
    assert sigmoid(z) == pytest.approx(expected_sigmoid(z), rel=1e-12)


@pytest.mark.id("tst_x5lrsd")
def test_big_inputs():
    """Big inputs don't overflow"""
    z = np.array([-1000.0, -50.0, 50.0, 1000.0])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        p = sigmoid(z)
    assert p == pytest.approx(expected_sigmoid(z), rel=1e-12, abs=0)


@pytest.mark.id("tst_mju84p")
def test_symmetric_about_zero():
    """Symmetric about zero"""
    z = np.linspace(-30, 30, 61)
    gap = np.max(np.abs(sigmoid(-z) + sigmoid(z) - 1))
    assert gap <= 1e-12, "sigmoid(-z) + sigmoid(z) should be 1 for every z"


@pytest.mark.id("tst_s84kpo")
def test_three_samples():
    """Three samples"""
    X = np.array([[1.0, 2.0], [0.0, 0.0], [-1.0, 0.5]])
    w = np.array([0.5, -0.25])
    p = predict_proba(X, w, 0.1)
    assert p == pytest.approx(expected_sigmoid(X @ w + 0.1), rel=1e-12)


@pytest.mark.id("tst_x9dsc4")
def test_one_probability_per_sample():
    """One probability per sample"""
    X = training_features()
    p = predict_proba(X, np.zeros(X.shape[1]), 0.0)
    assert p.shape == (len(X),)
    assert p == pytest.approx(np.full(len(X), 0.5))
