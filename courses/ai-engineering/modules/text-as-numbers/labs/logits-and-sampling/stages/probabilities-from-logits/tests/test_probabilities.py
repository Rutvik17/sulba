import numpy as np
import pytest
from scipy import special

from judge import load_pairs, log_softmax, shares, softmax


def logits_to_try():
    """Random logits at three scales, and the logits the file keeps."""
    rng = np.random.default_rng(0)
    _, _, kept = load_pairs()
    return [rng.normal(0, scale, size=(50, 20)) for scale in [1, 10, 100]] + [kept]


@pytest.mark.id("tst_my0smw")
def test_log_softmax():
    """Matches SciPy's log_softmax"""
    for logits in logits_to_try():
        wanted = special.log_softmax(logits, axis=-1)
        np.testing.assert_allclose(log_softmax(logits), wanted, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(
            log_softmax(logits[0]), wanted[0], rtol=1e-12, atol=1e-12
        )


@pytest.mark.id("tst_8boh0d")
def test_softmax():
    """Matches SciPy's softmax, and adds up to 1"""
    for logits in logits_to_try():
        found = softmax(logits)
        np.testing.assert_allclose(found, special.softmax(logits, axis=-1), atol=1e-12)
        np.testing.assert_allclose(found.sum(axis=-1), 1, rtol=1e-12)


@pytest.mark.id("tst_isf5bu")
def test_extremes():
    """Large logits, and removed ones"""
    np.testing.assert_allclose(log_softmax(np.array([1000.0, 1.0])), [0.0, -999.0])
    np.testing.assert_allclose(
        softmax(np.array([-1000.0, -1001.0])), special.expit([1, -1])
    )
    removed = np.array([2.0, -np.inf, 2.0])
    found = softmax(removed)
    np.testing.assert_allclose(found, [0.5, 0.0, 0.5], rtol=1e-12)
    assert found[1] == 0
    assert log_softmax(removed)[1] == -np.inf


@pytest.mark.id("tst_k2vsr3")
def test_shares():
    """Each answer's share of all the probability"""
    pairs, _, _ = load_pairs()
    found = shares(pairs)
    yes = np.exp(pairs["yes"].to_numpy() - pairs["lse"].to_numpy())
    no = np.exp(pairs["no"].to_numpy() - pairs["lse"].to_numpy())
    np.testing.assert_allclose(found["yes"], yes, rtol=1e-12)
    np.testing.assert_allclose(found["no"], no, rtol=1e-12)
    np.testing.assert_allclose(found["other"], 1 - yes - no, rtol=1e-9, atol=1e-15)
