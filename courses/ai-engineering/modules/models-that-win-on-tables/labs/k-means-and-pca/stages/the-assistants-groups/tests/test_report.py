import numpy as np
import pandas as pd
import pytest

from report import MEASUREMENTS, group_names, plot_axes, run, scale


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0]
    harvest = table[table["set"] == 1].head(40)
    return (
        train[MEASUREMENTS].to_numpy(dtype=float),
        train["variety"].to_numpy(),
        harvest[MEASUREMENTS].to_numpy(dtype=float),
    )


@pytest.mark.id("tst_mv1eqv")
def test_scale(beans):
    """Each training measurement scaled to a mean of 0 and a standard deviation of 1"""
    X, _, _ = beans
    Z, _ = scale(X, X)
    np.testing.assert_allclose(Z.mean(axis=0), 0, atol=1e-9)
    np.testing.assert_allclose(Z.std(axis=0), 1, rtol=1e-9)


@pytest.mark.id("tst_j2d0qo")
def test_plot_axes(beans):
    """Two directions of length 1 at right angles, and a share between 0 and 1"""
    X, _, _ = beans
    Z, _ = scale(X, X)
    directions, share = plot_axes(Z)
    np.testing.assert_allclose(directions @ directions.T, np.eye(2), atol=1e-9)
    assert 0 < share < 1


@pytest.mark.id("tst_koi02g")
def test_group_names():
    """A name for each group, a variety of its own beans"""
    labels = np.array([0, 0, 1, 1, 1])
    varieties = np.array(["SEKER", "SEKER", "SIRA", "SIRA", "SEKER"])
    names = group_names(labels, varieties)
    assert len(names) == 2
    for group, name in enumerate(names):
        assert name in varieties[labels == group]


@pytest.mark.id("tst_2z1qfm")
def test_run(beans):
    """A name for each bean of the harvest"""
    X, varieties, harvest = beans
    _, _, names = run(X, varieties, harvest)
    assert len(names) == len(harvest)
    assert set(names) <= set(varieties)
