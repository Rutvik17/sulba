import random

import pytest
from scipy import stats

from estimates import mean, quantile


def triangular(low, likely, high):
    """SciPy's triangular distribution for the three estimates."""
    return stats.triang((likely - low) / (high - low), loc=low, scale=high - low)


@pytest.mark.id("tst_cn4eas")
def test_sign_in():
    """Gives the mean and the 80% days of signing in"""
    assert mean(3, 5, 12) == pytest.approx(20 / 3)
    assert quantile(3, 5, 12, 0.8) == pytest.approx(triangular(3, 5, 12).ppf(0.8))


@pytest.mark.id("tst_obm4xa")
def test_edges():
    """Gives the ends at chances 0 and 1, and the days of a task whose estimates are equal"""
    assert quantile(2, 4, 9, 0) == pytest.approx(2)
    assert quantile(2, 4, 9, 1) == pytest.approx(9)
    assert quantile(2, 2, 9, 0.5) == pytest.approx(triangular(2, 2, 9).ppf(0.5))
    assert quantile(2, 9, 9, 0.5) == pytest.approx(triangular(2, 9, 9).ppf(0.5))
    assert quantile(5, 5, 5, 0.3) == 5
    assert mean(5, 5, 5) == 5


@pytest.mark.id("tst_ei2z6d")
def test_random():
    """Matches SciPy's triang, on random estimates and chances"""
    rng = random.Random(301)
    for _ in range(300):
        low, likely, high = sorted(rng.uniform(0, 30) for _ in range(3))
        if high - low < 1e-6:
            continue
        q = rng.random()
        shape = triangular(low, likely, high)
        assert mean(low, likely, high) == pytest.approx(shape.mean())
        assert quantile(low, likely, high, q) == pytest.approx(shape.ppf(q), abs=1e-9)
