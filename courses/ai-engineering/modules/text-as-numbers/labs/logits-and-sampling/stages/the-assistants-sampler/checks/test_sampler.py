import numpy as np
import pytest

import judge
from sampler import TOP_K, label, sample, warp

# The file's pairs each check takes.
PAIRS = 200


@pytest.fixture(scope="module")
def logits():
    """Pairs from the file with no two logits tied."""
    _, _, kept = judge.load_pairs()
    return [values for values in kept if len(set(values)) == len(values)][:PAIRS]


def assert_like_generation(logits, temperature, top_p):
    found = [warp(values, temperature, TOP_K, top_p) for values in logits]
    wanted = [judge.warp(values, temperature, TOP_K, top_p) for values in logits]
    np.testing.assert_allclose(found, wanted, rtol=1e-9, atol=1e-12)


@pytest.mark.id("tst_h7ddrh")
def test_temperature(logits):
    """Temperature as generation applies it"""
    for temperature in [0.4, 0.7, 1.5]:
        assert_like_generation(logits, temperature, 1.0)


@pytest.mark.id("tst_acw01r")
def test_top_p(logits):
    """Top-p keeps the token that reaches p"""
    for top_p in [0.5, 0.8, 0.9]:
        assert_like_generation(logits, 1.0, top_p)


@pytest.mark.id("tst_yzwiog")
def test_weights():
    """Draws each token with its probability"""
    rng = np.random.default_rng(2)
    for probabilities in [[0.9, 0.1], [0.6, 0.3, 0.1], [0.25, 0.0, 0.75]]:
        probabilities = np.array(probabilities)
        draws = [sample(probabilities, rng) for _ in range(4000)]
        shares = np.bincount(draws, minlength=len(probabilities)) / len(draws)
        np.testing.assert_allclose(shares, probabilities, atol=0.03)


@pytest.mark.id("tst_z0gywp")
def test_independent():
    """Each pair drawn with its own random number"""
    values = np.array([5.0, 5.0] + [-np.inf] * 18)
    row = np.array(["Yes", "No"] + ["The"] * 18, dtype=object)
    labels = label([row] * 400, [values] * 400, top_p=1.0)
    assert 150 <= labels.count("Yes") <= 250
