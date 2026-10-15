import numpy as np
import pytest
from scipy.optimize import approx_fprime
from scipy.spatial.distance import cdist

from gradients import numerical_gradient, relative_error


@pytest.fixture(scope="module")
def clinic():
    """The first new sample and its nearest record, standardized."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    records, sample = (X - mean) / std, (table[new, 2:][0] - mean) / std
    return sample, records[np.argmin(cdist(sample[None, :], records)[0])]


@pytest.mark.id("tst_ri85e6")
def test_small_case():
    """The gradient of x₀² + 3x₀x₁ at (1, 2), worked by hand"""
    found = numerical_gradient(
        lambda v: v[0] * v[0] + 3 * v[0] * v[1], np.array([1.0, 2.0])
    )
    assert np.allclose(found, [8, 3], rtol=0, atol=1e-8)


@pytest.mark.id("tst_89vka2")
def test_x_kept():
    """The point it's given stays as it was"""
    x = np.array([0.5, -1.25, 3.0])
    kept = x.copy()
    numerical_gradient(lambda v: float(np.sum(v**3)), x)
    assert np.array_equal(x, kept)


@pytest.mark.id("tst_aaan6m")
def test_distance_gradient(clinic):
    """The gradient of the distance to the nearest record: the unit vector away from it"""
    sample, record = clinic
    found = np.asarray(
        numerical_gradient(lambda v: np.sqrt(np.sum((v - record) ** 2)), sample.copy())
    )
    exact = (sample - record) / np.sqrt(np.sum((sample - record) ** 2))
    assert found.shape == sample.shape
    assert np.allclose(found, exact, rtol=0, atol=1e-8)


@pytest.mark.id("tst_1g6fc2")
def test_close_to_scipy(clinic):
    """Close to SciPy's approx_fprime"""
    sample, record = clinic

    def distance(v):
        return np.sqrt(np.sum((v - record) ** 2))

    found = np.asarray(numerical_gradient(distance, sample.copy()))
    assert np.allclose(found, approx_fprime(sample.copy(), distance), rtol=0, atol=1e-6)


@pytest.mark.id("tst_yomb10")
def test_relative_errors():
    """Relative errors, worked by hand"""
    assert relative_error([3.0, 4.0], [3.0, 4.0]) == 0
    assert relative_error([3.0, 4.0], [0.0, 0.0]) == pytest.approx(1)
    assert relative_error([1.0, 0.0], [0.0, 1.0]) == pytest.approx(np.sqrt(2))
    assert relative_error([2.0, 0.0], [1.0, 0.0]) == pytest.approx(0.5)
    assert relative_error([0.0, 0.0], [0.0, 0.0]) == 0
    assert relative_error([3e-9, 4e-9], [3e-9, 0.0]) == pytest.approx(0.8)
