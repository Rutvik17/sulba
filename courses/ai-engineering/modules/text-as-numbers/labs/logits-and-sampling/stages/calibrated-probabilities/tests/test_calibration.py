import numpy as np
import pandas as pd
import pytest

from judge import calibrate, load_pairs, match_probability


@pytest.mark.id("tst_7e3e05")
def test_yes_among_two():
    """The judge's probability of Yes among Yes and No"""
    pairs, _, _ = load_pairs()
    yes = np.exp(pairs["yes"] - pairs["lse"]).to_numpy()
    no = np.exp(pairs["no"] - pairs["lse"]).to_numpy()
    np.testing.assert_allclose(match_probability(pairs), yes / (yes + no), rtol=1e-9)


@pytest.mark.id("tst_ppzm61")
def test_order():
    """A wider margin for Yes, a higher probability"""
    pairs = pd.DataFrame({"yes": [1.0, 2.0, 4.0, 8.0], "no": [2.0, 2.0, 2.0, 2.0]})
    for temperature, shift in [(1.0, 0.0), (5.0, -0.5), (0.5, 2.0)]:
        assert np.all(np.diff(match_probability(pairs, temperature, shift)) > 0)


@pytest.mark.id("tst_1vleh1")
def test_known_fit():
    """Finds the temperature and shift that labels were drawn with"""
    rng = np.random.default_rng(0)
    margin = rng.uniform(-20, 20, 20_000)
    exact = rng.random(len(margin)) < 1 / (1 + np.exp(-(margin / 5 - 0.5)))
    pairs = pd.DataFrame({"yes": margin, "no": 0.0, "label": np.where(exact, "E", "I")})
    temperature, shift = calibrate(pairs)
    assert temperature == pytest.approx(5, rel=0.05)
    assert shift == pytest.approx(-0.5, abs=0.1)
