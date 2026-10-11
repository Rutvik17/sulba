import numpy as np
import pytest
from scale import standardize


@pytest.mark.id("tst_nump01")
def test_mean_zero():
    """Standardized values have mean 0"""
    assert standardize(np.array([1.0, 2.0, 6.0])).mean() == pytest.approx(0.0)


@pytest.mark.id("tst_nump02")
def test_population_spread():
    """Standardized values use the population standard deviation"""
    np.testing.assert_allclose(standardize(np.array([1.0, 3.0])), [-1.0, 1.0])
