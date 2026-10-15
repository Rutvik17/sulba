import numpy as np
import pytest

from report import Screen, candidates


@pytest.fixture(scope="module")
def survey():
    """The training candidates and the test candidates."""
    table = np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)
    return candidates(table, 0), candidates(table, 2)


@pytest.mark.id("tst_4w4t8m")
def test_probability_for_each_candidate(survey):
    """One probability for each candidate, from 0 to 1"""
    (X_train, y_train), (X, _) = survey
    p = np.asarray(Screen(X_train, y_train, 0.02).probabilities(X), dtype=float)
    assert p.shape == (len(X),)
    assert np.all((p >= 0) & (p <= 1))


@pytest.mark.id("tst_f67nly")
def test_rarer_pulsars_lower_probabilities(survey):
    """Where pulsars are rarer, every probability is lower"""
    (X_train, y_train), (X, _) = survey
    rare = np.asarray(Screen(X_train, y_train, 0.01).probabilities(X), dtype=float)
    common = np.asarray(Screen(X_train, y_train, 0.2).probabilities(X), dtype=float)
    assert np.all(rare <= common)
    assert np.mean(rare) < np.mean(common)


@pytest.mark.id("tst_z16hku")
def test_follow_ups_most_likely_first(survey):
    """The follow-ups are the most likely pulsars, most likely first"""
    (X_train, y_train), (X, _) = survey
    screen = Screen(X_train, y_train, 0.02)
    p = np.asarray(screen.probabilities(X), dtype=float)
    chosen = np.asarray(screen.follow_ups(X, 50), dtype=int)
    assert chosen.shape == (50,)
    assert len(set(chosen.tolist())) == 50
    assert np.all(np.diff(p[chosen]) <= 0)
    rest = np.setdiff1d(np.arange(len(X)), chosen)
    assert p[rest].max() <= p[chosen].min()


@pytest.mark.id("tst_3u6unz")
def test_budget_past_the_candidates(survey):
    """A budget past the number of candidates gives every candidate"""
    (X_train, y_train), (X, _) = survey
    chosen = np.asarray(
        Screen(X_train, y_train, 0.02).follow_ups(X[:20], 50), dtype=int
    )
    assert sorted(chosen.tolist()) == list(range(20))
