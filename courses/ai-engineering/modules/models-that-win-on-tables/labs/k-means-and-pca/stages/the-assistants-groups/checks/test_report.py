import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from report import (
    MEASUREMENTS,
    fit_groups,
    group_names,
    harvest_groups,
    plot_axes,
    scale,
)

# The checks' own groups: as many, from as many starts, as the report's.
K, STARTS, SEED = 9, 10, 0


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0]
    harvest = table[table["set"] == 1]
    X = train[MEASUREMENTS].to_numpy(dtype=float)
    V = harvest[MEASUREMENTS].to_numpy(dtype=float)
    Z, H = scale(X, V)
    model = KMeans(K, n_init=STARTS, random_state=SEED).fit(Z)
    return X, V, Z, H, train["variety"].to_numpy(), model


@pytest.mark.id("tst_fp9xb9")
def test_most_variance(beans):
    """The plot along the directions that vary most"""
    _, _, Z, _, _, _ = beans
    directions, share = plot_axes(Z)
    model = PCA(n_components=2).fit(Z)
    assert share == pytest.approx(model.explained_variance_ratio_.sum(), rel=1e-9)
    alike = np.abs((directions * model.components_).sum(axis=1))
    np.testing.assert_allclose(alike, 1, atol=1e-8)


@pytest.mark.id("tst_uy93cd")
def test_scaled_groups(beans):
    """Groups of the scaled measurements"""
    X, _, Z, _, _, _ = beans
    model = fit_groups(X)
    assert model.predict(Z).tolist() == model.labels_.tolist()


@pytest.mark.id("tst_sqktcb")
def test_names(beans):
    """Each group named by its commonest variety"""
    _, _, _, _, varieties, model = beans
    names = group_names(model.labels_, varieties)
    for group in range(K):
        counts = pd.Series(varieties[model.labels_ == group]).value_counts()
        assert names[group] == counts.index[0]


@pytest.mark.id("tst_73q1ow")
def test_harvest(beans):
    """Each harvest bean in the group of its nearest training centre"""
    X, V, _, H, _, model = beans
    assert harvest_groups(model, X, V).tolist() == model.predict(H).tolist()
