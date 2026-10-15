import numpy as np
import pytest

from tuning import DEGREES, PENALTIES, choose, expected_error, records, scores, tuned


@pytest.fixture(scope="module")
def plant():
    """The plant's records of its first 100 mixes, to keep the tests fast: (X, y, mixes)."""
    X, y, mixes = records(np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1))
    first = mixes < 100
    return X[first], y[first], mixes[first]


@pytest.mark.id("tst_8wsibn")
def test_chooses_a_pair_it_tried(plant):
    """Chooses a degree and penalty it tried"""
    degree, penalty = choose(scores(*plant))
    assert degree in DEGREES
    assert penalty in PENALTIES


@pytest.mark.id("tst_q3llwg")
def test_expected_error_in_mpa(plant):
    """The expected error is a number of MPa"""
    error = expected_error(*plant)
    assert 0 < error < 20


@pytest.mark.id("tst_0voyt0")
def test_strength_for_each_test(plant):
    """The tuned model gives a strength for each test"""
    X, y, mixes = plant
    strengths = np.asarray(tuned(X, y, mixes)(X[:10]), dtype=float)
    assert strengths.shape == (10,)
    assert np.all(np.isfinite(strengths))
