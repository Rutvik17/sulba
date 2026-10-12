import numpy as np
import pytest
from classify import fit

X = np.array([[0.0], [1.0], [3.0], [4.0]])
y = np.array([0, 0, 1, 1])


@pytest.mark.id("tst_skln01")
def test_separates_two_groups():
    """Separates two groups"""
    assert fit(X, y).predict(X).tolist() == [0, 0, 1, 1]


@pytest.mark.id("tst_skln02")
def test_one_probability_per_sample():
    """Gives one probability per sample"""
    assert fit(X, y).predict_proba(X).shape == (4,)
