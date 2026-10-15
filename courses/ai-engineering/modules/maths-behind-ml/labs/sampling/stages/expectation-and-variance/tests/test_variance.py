import numpy as np
import pytest
from scipy.stats import hypergeom

from sampling import batch_mean_variance, simulated_means


@pytest.fixture(scope="module")
def records():
    """The records' worst areas and diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    with open("data/breast-cancer.csv") as file:
        j = file.readline().strip().split(",").index("worst_area")
    return table[table[:, 0] == 0, j], table[table[:, 0] == 0, 1]


@pytest.mark.id("tst_f3qpro")
def test_same_as_hypergeometric(records):
    """The same as SciPy's hypergeometric distribution, for a batch's share malignant"""
    _, y = records
    n, malignant = len(y), int(y.sum())
    for size in (8, 32, 128):
        expected = hypergeom(n, malignant, size).var() / size**2
        assert batch_mean_variance(y, size) == pytest.approx(expected, rel=1e-12)


@pytest.mark.id("tst_yf0kaa")
def test_one_row_and_every_row(records):
    """A batch of one row varies as much as the values, and a batch of every row not at all"""
    area, _ = records
    assert batch_mean_variance(area, 1) == pytest.approx(np.var(area), rel=1e-12)
    assert batch_mean_variance(area, len(area)) == pytest.approx(0, abs=1e-9)


@pytest.mark.id("tst_l2mhu3")
def test_simulation_agrees(records):
    """Simulated batch shares average to the records' share, and vary as the formula says"""
    _, y = records
    means = np.asarray(simulated_means(y, 32, np.random.default_rng(2), 4000))
    assert means.shape == (4000,)
    assert abs(means.mean() - y.mean()) < 4 * np.sqrt(batch_mean_variance(y, 32) / 4000)
    assert np.var(means) == pytest.approx(batch_mean_variance(y, 32), rel=0.1)


@pytest.mark.id("tst_l5mkxj")
def test_measurement(records):
    """Simulated batch means of worst area vary as the formula says, in batches of 200"""
    area, _ = records
    means = np.asarray(simulated_means(area, 200, np.random.default_rng(1), 4000))
    assert np.var(means) == pytest.approx(batch_mean_variance(area, 200), rel=0.1)


@pytest.mark.id("tst_tsfecx")
def test_every_record(records):
    """A simulated batch of every record has the records' mean, every time"""
    area, _ = records
    means = np.asarray(simulated_means(area, len(area), np.random.default_rng(4), 20))
    assert means == pytest.approx(np.full(20, area.mean()), rel=1e-12)


@pytest.mark.id("tst_jbqt1o")
def test_reproducible(records):
    """The same seed gives the same simulation"""
    _, y = records
    first = np.asarray(simulated_means(y, 8, np.random.default_rng(3), 50))
    again = np.asarray(simulated_means(y, 8, np.random.default_rng(3), 50))
    assert np.array_equal(first, again)
