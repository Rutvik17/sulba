import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

from sorter import MEASUREMENTS, scale


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0][MEASUREMENTS].to_numpy()
    test = table[table["set"] == 2][MEASUREMENTS].to_numpy()
    return train, test


@pytest.mark.id("tst_7n8b7f")
def test_scikit_learn(beans):
    """The same as scikit-learn's StandardScaler fitted on the training beans"""
    train, test = beans
    scaler = StandardScaler().fit(train)
    train_scaled, test_scaled = scale(train, test)
    np.testing.assert_allclose(
        train_scaled, scaler.transform(train), rtol=0, atol=1e-12
    )
    np.testing.assert_allclose(test_scaled, scaler.transform(test), rtol=0, atol=1e-12)


@pytest.mark.id("tst_steaep")
def test_one_bean(beans):
    """A bean scaled alone as it is among the others"""
    train, test = beans
    _, alone = scale(train, test[:1])
    _, together = scale(train, test)
    np.testing.assert_allclose(alone, together[:1], rtol=0, atol=1e-12)


@pytest.mark.id("tst_hrmu0z")
def test_units(beans):
    """The same scaled values with the areas in other units"""
    train, test = beans
    # Square millimetres for the two areas, were each pixel 0.01 mm square.
    units = np.ones(len(MEASUREMENTS))
    units[[MEASUREMENTS.index("Area"), MEASUREMENTS.index("ConvexArea")]] = 0.01
    in_pixels = scale(train, test)
    in_millimetres = scale(train * units, test * units)
    for pixels, millimetres in zip(in_pixels, in_millimetres):
        np.testing.assert_allclose(millimetres, pixels, rtol=0, atol=1e-9)


@pytest.mark.id("tst_ih13bs")
def test_unchanged(beans):
    """The arrays given left as they were"""
    train, test = beans
    train_copy, test_copy = train.copy(), test.copy()
    scale(train, test)
    np.testing.assert_array_equal(train, train_copy)
    np.testing.assert_array_equal(test, test_copy)
