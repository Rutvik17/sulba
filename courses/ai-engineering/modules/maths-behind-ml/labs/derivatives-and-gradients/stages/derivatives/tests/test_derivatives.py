import numpy as np
import pytest
from scipy.differentiate import derivative as scipy_derivative
from scipy.spatial.distance import cdist

from gradients import central_difference, derivative, forward_difference


@pytest.fixture(scope="module")
def texture():
    """The distance from the first new sample to its nearest record as the sample's worst
    texture moves by t standard deviations, the same for an array of t, and its exact
    derivative at 0."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    with open("data/breast-cancer.csv") as file:
        j = file.readline().strip().split(",")[2:].index("worst_texture")
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    records, sample = (X - mean) / std, (table[new, 2:][0] - mean) / std
    gap = sample - records[np.argmin(cdist(sample[None, :], records)[0])]
    rest = np.sum(np.delete(gap, j) ** 2)

    def distance(t):
        moved = gap[j] + t
        return float(np.sqrt(rest + moved * moved))

    def distances(t):
        moved = gap[j] + t
        return np.sqrt(rest + moved * moved)

    return distance, distances, gap[j] / distance(0.0)


@pytest.mark.id("tst_g5iyxg")
def test_small_case():
    """Both slopes of x², worked by hand"""
    assert forward_difference(lambda x: x * x, 3.0, 0.5) == pytest.approx(6.5)
    assert central_difference(lambda x: x * x, 3.0, 0.5) == pytest.approx(6.0)


@pytest.mark.id("tst_n8lkiv")
def test_quadratic_exact():
    """A central difference is exact for a quadratic, whatever the step"""
    for h in (0.1, 1.0, 10.0):
        found = central_difference(lambda x: 2 * x * x - 3 * x + 1, 1.5, h)
        assert found == pytest.approx(3.0, rel=0, abs=1e-9)


@pytest.mark.id("tst_5unwwh")
def test_distance_slopes(texture):
    """The distance's slope as worst texture changes, by each difference"""
    distance, _, exact = texture
    assert forward_difference(distance, 0.0, 1e-7) == pytest.approx(
        exact, rel=0, abs=1e-6
    )
    assert central_difference(distance, 0.0, 1e-5) == pytest.approx(
        exact, rel=0, abs=1e-9
    )


@pytest.mark.id("tst_ldx2fs")
def test_same_as_scipy(texture):
    """The same derivative as SciPy's scipy.differentiate.derivative"""
    distance, distances, _ = texture
    expected = float(scipy_derivative(distances, 0.0).df)
    assert derivative(distance, 0.0) == pytest.approx(expected, rel=0, abs=1e-9)


@pytest.mark.id("tst_o9bjhd")
def test_step_suited_to_x():
    """Right for x³ at 2, and at a million either way, where a fixed step isn't"""
    for x in (2.0, 1e6, -1e6):
        assert derivative(lambda t: t * t * t, x) == pytest.approx(3 * x * x, rel=1e-9)
