import numpy as np
import pytest
from sklearn.neighbors import NearestCentroid

from vectors import direction, scores


@pytest.fixture(scope="module")
def clinic():
    """The records, standardized, their diagnoses and class means, and the new samples."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X, y = table[~new, 2:], table[~new, 1]
    mean, std = X.mean(axis=0), X.std(axis=0)
    Z = (X - mean) / std
    mu0, mu1 = Z[y == 0].mean(axis=0), Z[y == 1].mean(axis=0)
    return Z, y, mu0, mu1, (table[new, 2:] - mean) / std


@pytest.mark.id("tst_nsbf08")
def test_unit_direction():
    """A vector of length 1, from one point toward the other"""
    u = np.asarray(direction(np.array([1.0, 1.0]), np.array([4.0, 5.0])))
    assert np.allclose(u, [0.6, 0.8], rtol=0, atol=1e-12)


@pytest.mark.id("tst_q21x64")
def test_small_case():
    """Three points, worked by hand"""
    mu0, mu1 = np.array([0.0, 0.0]), np.array([2.0, 0.0])
    Z = np.array([[3.0, 5.0], [1.0, -2.0], [0.0, 0.0]])
    assert np.allclose(scores(Z, mu0, mu1), [2, 0, -1], rtol=0, atol=1e-12)


@pytest.mark.id("tst_z7oce7")
def test_nearest_centroid(clinic):
    """Above 0 exactly where scikit-learn's NearestCentroid finds the malignant mean nearer"""
    Z, y, mu0, mu1, new = clinic
    found = np.asarray(scores(new.copy(), mu0.copy(), mu1.copy()))
    assert found.shape == (len(new),)
    nearer = NearestCentroid().fit(Z, y).predict(new) == 1
    assert np.array_equal(found > 0, nearer)


@pytest.mark.id("tst_08d808")
def test_difference_of_squared_distances(clinic):
    """Half the difference of the squared distances to the two means, over their distance apart"""
    _, _, mu0, mu1, new = clinic
    to0 = np.sum((new - mu0) ** 2, axis=1)
    to1 = np.sum((new - mu1) ** 2, axis=1)
    expected = (to0 - to1) / (2 * np.linalg.norm(mu1 - mu0))
    assert np.allclose(scores(new, mu0, mu1), expected, rtol=1e-9, atol=1e-12)


@pytest.mark.id("tst_jabv7p")
def test_one_at_a_time(clinic):
    """A sample scores the same alone as in a batch"""
    _, _, mu0, mu1, new = clinic
    batch = np.asarray(scores(new, mu0, mu1))
    for i in (0, 57, 113):
        alone = np.asarray(scores(new[[i]], mu0, mu1))
        assert alone.shape == (1,)
        assert alone[0] == pytest.approx(batch[i], rel=1e-12, abs=1e-12)
