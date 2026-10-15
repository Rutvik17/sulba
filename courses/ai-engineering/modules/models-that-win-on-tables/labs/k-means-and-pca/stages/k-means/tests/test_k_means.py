import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans

from groups import MEASUREMENTS, assign, k_means, scale

# Four points on a line, and the two centres k-means starts from.
LINE = np.array([[0.0], [1.0], [10.0], [11.0]])
STARTS = np.array([[0.0], [1.0]])


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0][MEASUREMENTS].to_numpy(dtype=float)
    Z, _ = scale(train, train)
    return Z


@pytest.mark.id("tst_7kykgk")
def test_by_hand():
    """Four points by hand"""
    labels, centres, inertia = k_means(LINE, STARTS)
    assert labels.tolist() == [0, 0, 1, 1]
    np.testing.assert_allclose(centres, [[0.5], [10.5]])
    assert inertia == pytest.approx(1.0)


@pytest.mark.id("tst_rrlw5f")
def test_tie():
    """A row as near two centres goes to the first"""
    found = assign(np.array([[1.0, 0.0]]), np.array([[0.0, 0.0], [2.0, 0.0]]))
    assert found.tolist() == [0]


@pytest.mark.id("tst_1n57d7")
def test_beans(beans):
    """The beans' groups as scikit-learn's KMeans finds them"""
    for k, seed in [(3, 1), (7, 0)]:
        rng = np.random.default_rng(seed)
        starts = beans[rng.choice(len(beans), k, replace=False)]
        labels, centres, inertia = k_means(beans, starts)
        model = KMeans(k, init=starts, n_init=1, tol=0, algorithm="lloyd").fit(beans)
        assert labels.tolist() == model.labels_.tolist()
        np.testing.assert_allclose(centres, model.cluster_centers_, rtol=0, atol=1e-9)
        assert inertia == pytest.approx(model.inertia_, rel=1e-9)


@pytest.mark.id("tst_c2zgh7")
def test_starts_kept():
    """The centres it starts from left as they were"""
    starts = STARTS.copy()
    k_means(LINE, starts)
    np.testing.assert_array_equal(starts, STARTS)
