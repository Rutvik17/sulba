import numpy as np
import pytest

from judge import answers, load_pairs, sample, warp

# The model's own temperature, top-k and top-p.
SETTINGS = (0.7, 20, 0.8)


@pytest.mark.id("tst_4yfs35")
def test_like_choice():
    """Draws what rng.choice draws"""
    for seed in range(100):
        rng = np.random.default_rng(seed)
        probabilities = rng.dirichlet(np.ones(20))
        removed = rng.random(20) < 0.3
        removed[rng.integers(20)] = False
        probabilities[removed] = 0
        probabilities /= probabilities.sum()
        mine = np.random.default_rng(seed + 100)
        numpys = np.random.default_rng(seed + 100)
        for _ in range(50):
            assert sample(probabilities, mine) == numpys.choice(20, p=probabilities)


@pytest.mark.id("tst_ci3pvj")
def test_removed():
    """Never draws a removed token"""
    _, _, logits = load_pairs()
    rng = np.random.default_rng(0)
    for values in logits[:50]:
        probabilities = warp(values, 1.0, 3)
        for _ in range(20):
            assert probabilities[sample(probabilities, rng)] > 0


@pytest.mark.id("tst_qjp6cf")
def test_answers():
    """One answer for each pair, drawn in order"""
    _, tokens, logits = load_pairs()
    found = answers(tokens, logits, np.random.default_rng(3), *SETTINGS)
    rng = np.random.default_rng(3)
    wanted = [
        row[rng.choice(len(values), p=warp(values, *SETTINGS))]
        for row, values in zip(tokens, logits, strict=True)
    ]
    assert list(found) == wanted


@pytest.mark.id("tst_wcvr37")
def test_seed():
    """The same answers from the same seed"""
    _, tokens, logits = load_pairs()
    first = answers(tokens, logits, np.random.default_rng(7), *SETTINGS)
    again = answers(tokens, logits, np.random.default_rng(7), *SETTINGS)
    other = answers(tokens, logits, np.random.default_rng(8), *SETTINGS)
    assert list(first) == list(again)
    assert list(first) != list(other)
