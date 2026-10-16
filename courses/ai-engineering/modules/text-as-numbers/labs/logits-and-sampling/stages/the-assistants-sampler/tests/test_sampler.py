import numpy as np
import pytest

from judge import load_pairs
from sampler import label, sample, warp


@pytest.fixture(scope="module")
def pairs():
    _, tokens, logits = load_pairs()
    return tokens[:100], logits[:100]


@pytest.mark.id("tst_tlpytv")
def test_sums(pairs):
    """Probabilities that add up to 1"""
    _, logits = pairs
    for values in logits:
        probabilities = warp(values)
        assert np.all(probabilities >= 0)
        assert probabilities.sum() == pytest.approx(1)


@pytest.mark.id("tst_og9cb1")
def test_top_k():
    """Keeps no more tokens than top-k"""
    logits = np.array([4.0, 3.0, 2.0, 1.0, 0.0])
    assert np.count_nonzero(warp(logits, top_k=2, top_p=1.0)) == 2


@pytest.mark.id("tst_zojfz4")
def test_kept_only():
    """Draws only tokens it kept"""
    rng = np.random.default_rng(1)
    probabilities = np.array([0.0, 0.7, 0.0, 0.3])
    for _ in range(100):
        assert sample(probabilities, rng) in (1, 3)


@pytest.mark.id("tst_u890s4")
def test_same_labels(pairs):
    """The same labels on every run"""
    tokens, logits = pairs
    assert label(tokens, logits) == label(tokens, logits)


@pytest.mark.id("tst_481m0r")
def test_answers(pairs):
    """Answers Yes or No at the model's settings"""
    tokens, logits = pairs
    assert set(label(tokens, logits)) <= {"Yes", "No"}
