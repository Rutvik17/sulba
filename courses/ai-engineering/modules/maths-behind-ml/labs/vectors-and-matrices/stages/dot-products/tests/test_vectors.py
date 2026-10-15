import numpy as np
import pytest
from scipy.spatial import distance
from sklearn.neighbors import NearestCentroid

from vectors import centroids, cosine, dot, norm


@pytest.fixture(scope="module")
def records():
    """The records, standardized, and their diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    X, y = table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]
    return (X - X.mean(axis=0)) / X.std(axis=0), y


@pytest.mark.id("tst_rt92e6")
def test_small_case():
    """Two small vectors, worked by hand"""
    a, b = np.array([1.0, 2.0, 3.0]), np.array([4.0, 5.0, 6.0])
    assert dot(a, b) == 32
    assert norm(np.array([3.0, 4.0])) == 5


@pytest.mark.id("tst_ke4d17")
def test_same_as_numpy(records):
    """The same dot products and lengths as NumPy's, for records"""
    Z, _ = records
    for i, j in [(0, 1), (5, 300), (17, 17), (454, 2)]:
        assert dot(Z[i].copy(), Z[j].copy()) == pytest.approx(
            np.dot(Z[i], Z[j]), rel=1e-12
        )
        assert norm(Z[i].copy()) == pytest.approx(np.linalg.norm(Z[i]), rel=1e-12)


@pytest.mark.id("tst_lszmng")
def test_cosines(records):
    """1 for the same direction, 0 at a right angle, -1 for opposite ones, and SciPy's for records"""
    a = np.array([2.0, 0.0])
    assert cosine(a, np.array([5.0, 0.0])) == pytest.approx(1)
    assert cosine(a, np.array([0.0, 3.0])) == pytest.approx(0)
    assert cosine(a, np.array([-1.0, 0.0])) == pytest.approx(-1)
    Z, _ = records
    for i, j in [(0, 1), (5, 300), (454, 2)]:
        expected = 1 - distance.cosine(Z[i], Z[j])
        assert cosine(Z[i].copy(), Z[j].copy()) == pytest.approx(
            expected, rel=1e-9, abs=1e-12
        )


@pytest.mark.id("tst_z5rnqd")
def test_small_centroids():
    """Each class's mean row, worked by hand"""
    Z = np.array([[0.0, 2.0], [2.0, 4.0], [6.0, 0.0]])
    mu0, mu1 = centroids(Z, np.array([0, 0, 1]))
    assert np.asarray(mu0).tolist() == [1, 3]
    assert np.asarray(mu1).tolist() == [6, 0]


@pytest.mark.id("tst_ywjr65")
def test_same_as_scikit_learn(records):
    """The same class means as scikit-learn's NearestCentroid"""
    Z, y = records
    mu0, mu1 = centroids(Z.copy(), y.copy())
    expected = NearestCentroid().fit(Z, y).centroids_
    assert np.allclose(mu0, expected[0], rtol=0, atol=1e-12)
    assert np.allclose(mu1, expected[1], rtol=0, atol=1e-12)
