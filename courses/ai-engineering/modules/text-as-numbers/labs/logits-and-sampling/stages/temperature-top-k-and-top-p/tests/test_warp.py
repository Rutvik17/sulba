import numpy as np
import pytest
from scipy import special

from judge import load_pairs, warp

# The file's pairs each test takes, and the random logits it adds.
PAIRS, RANDOM = 200, 100


def transformers_warp(logits, temperature, top_k, top_p):
    """The probabilities as transformers leaves them: its temperature, top-k and top-p
    warpers, in that order, then a softmax."""
    scores = np.asarray(logits, dtype=float) / temperature
    if top_k:
        kth = np.sort(scores)[-min(top_k, len(scores))]
        scores = np.where(scores < kth, -np.inf, scores)
    if top_p < 1:
        ascending = np.argsort(scores, kind="stable")
        cumulative = np.cumsum(special.softmax(scores[ascending]))
        removed = cumulative <= 1 - top_p
        removed[-1] = False
        scores[ascending[removed]] = -np.inf
    return special.softmax(scores)


@pytest.fixture(scope="module")
def logits():
    """Pairs from the file with no two logits tied, and random logits."""
    _, _, kept = load_pairs()
    distinct = [values for values in kept if len(set(values)) == len(values)]
    rng = np.random.default_rng(0)
    return distinct[:PAIRS] + list(rng.normal(0, 3, size=(RANDOM, 20)))


def assert_like_transformers(logits, temperature=1.0, top_k=0, top_p=1.0):
    found = [warp(values, temperature, top_k, top_p) for values in logits]
    wanted = [transformers_warp(values, temperature, top_k, top_p) for values in logits]
    np.testing.assert_allclose(found, wanted, rtol=1e-9, atol=1e-12)


@pytest.mark.id("tst_w8bcxy")
def test_temperature(logits):
    """Temperature divides the logits"""
    for temperature in [0.25, 0.7, 1.5, 3.0]:
        found = [warp(values, temperature) for values in logits]
        wanted = [special.softmax(values / temperature) for values in logits]
        np.testing.assert_allclose(found, wanted, rtol=1e-9, atol=1e-12)


@pytest.mark.id("tst_lypq9b")
def test_top_k(logits):
    """Top-k keeps the highest logits, and any tied with the k-th"""
    for top_k in [1, 2, 5, 19]:
        assert_like_transformers(logits, top_k=top_k)
    found = warp(np.array([5.0, 5.0, 5.0, 1.0]), top_k=2)
    np.testing.assert_allclose(found, [1 / 3, 1 / 3, 1 / 3, 0], rtol=1e-9)


@pytest.mark.id("tst_ln510p")
def test_top_p(logits):
    """Top-p keeps the fewest likeliest tokens that reach p"""
    for top_p in [0.5, 0.8, 0.95, 0.999]:
        assert_like_transformers(logits, top_p=top_p)
    found = warp(np.log([0.6, 0.3, 0.1]), top_p=0.8)
    np.testing.assert_allclose(found, [2 / 3, 1 / 3, 0], rtol=1e-9)
    np.testing.assert_allclose(warp(np.log([0.9, 0.1]), top_p=0.8), [1, 0])


@pytest.mark.id("tst_nnnjk2")
def test_in_order(logits):
    """All three, in transformers' order"""
    for settings in [(0.7, 20, 0.8), (1.5, 5, 0.9), (0.4, 3, 0.6), (2.0, 0, 0.95)]:
        assert_like_transformers(logits, *settings)
