import numpy as np
import pandas as pd
import pytest
from sklearn.decomposition import PCA

from groups import MEASUREMENTS, components, project, scale

# Six rows that vary most along the third column, then the second, then the first.
AXES = np.array(
    [[0, 0, 3], [0, 0, -3], [0, 2, 0], [0, -2, 0], [1, 0, 0], [-1, 0, 0]], dtype=float
)


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0][MEASUREMENTS].to_numpy(dtype=float)
    validation = table[table["set"] == 1][MEASUREMENTS].to_numpy(dtype=float)
    return scale(train, validation)


@pytest.mark.id("tst_2yabuf")
def test_by_hand():
    """Three columns by hand, the widest first"""
    variances, directions = components(AXES)
    np.testing.assert_allclose(variances, [3.6, 1.6, 0.4], rtol=1e-12)
    np.testing.assert_allclose(
        directions, [[0, 0, 1], [0, 1, 0], [1, 0, 0]], atol=1e-12
    )
    np.testing.assert_allclose(
        project(AXES[:3], directions), [[3, 0, 0], [-3, 0, 0], [0, 2, 0]], atol=1e-12
    )


@pytest.mark.id("tst_o1vz6r")
def test_beans(beans):
    """The beans' components as scikit-learn's PCA finds them"""
    Z, _ = beans
    variances, directions = components(Z)
    model = PCA().fit(Z)
    np.testing.assert_allclose(
        variances, model.explained_variance_, rtol=1e-9, atol=1e-12
    )
    # The last components have variances so small and close that their directions are
    # decided by rounding: the first four are compared.
    np.testing.assert_allclose(directions[:4], model.components_[:4], rtol=0, atol=1e-8)


@pytest.mark.id("tst_9fbqub")
def test_scores(beans):
    """The validation beans' scores as PCA's transform gives them"""
    Z, V = beans
    _, directions = components(Z)
    model = PCA(n_components=2).fit(Z)
    np.testing.assert_allclose(
        project(V, directions[:2]), model.transform(V), rtol=0, atol=1e-8
    )


@pytest.mark.id("tst_d8wge4")
def test_most_variance(beans):
    """No direction with more variance than the first"""
    Z, _ = beans
    variances, directions = components(Z)
    assert np.var(project(Z, directions[:1]), ddof=1) == pytest.approx(variances[0])
    rng = np.random.default_rng(0)
    tried = rng.normal(size=(500, len(MEASUREMENTS)))
    tried /= np.linalg.norm(tried, axis=1, keepdims=True)
    assert np.var(project(Z, tried), axis=0, ddof=1).max() <= variances[0]
