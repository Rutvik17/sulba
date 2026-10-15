import numpy as np
import pytest
from scipy.spatial.distance import cdist
from sklearn.neighbors import NearestCentroid

from screen import Screen

K = 5


@pytest.fixture(scope="module")
def clinic():
    """The records' measurements and diagnoses and the new samples, and the records and
    samples standardized with the records' mean and standard deviation."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    records, diagnoses, samples = table[~new, 2:], table[~new, 1], table[new, 2:]
    mean, std = records.mean(axis=0), records.std(axis=0)
    return records, diagnoses, samples, (records - mean) / std, (samples - mean) / std


def screen_of(clinic):
    """A screen made from copies of the records, so that no check sees another's."""
    records, diagnoses = clinic[0], clinic[1]
    return Screen(records.copy(), diagnoses.copy())


@pytest.mark.id("tst_wqtafv")
def test_in_standard_deviations(clinic):
    """A sample moved one standard deviation toward the malignant mean scores 1 more"""
    records, diagnoses, samples, Z, _ = clinic
    mu0, mu1 = Z[diagnoses == 0].mean(axis=0), Z[diagnoses == 1].mean(axis=0)
    u = (mu1 - mu0) / np.linalg.norm(mu1 - mu0)
    screen = screen_of(clinic)
    before = np.asarray(screen.scores(samples[:10].copy()))
    after = np.asarray(screen.scores(samples[:10] + u * records.std(axis=0)))
    assert np.allclose(after - before, 1, rtol=0, atol=1e-9)


@pytest.mark.id("tst_gpvuyv")
def test_above_zero_where_malignant_is_nearer(clinic):
    """Above 0 exactly where the malignant mean is nearer"""
    _, diagnoses, samples, Z, Zn = clinic
    scores = np.asarray(screen_of(clinic).scores(samples.copy()))
    nearer = NearestCentroid().fit(Z, diagnoses).predict(Zn) == 1
    assert np.array_equal(scores > 0, nearer)


@pytest.mark.id("tst_0wk722")
def test_distances(clinic):
    """Each record shown at its distance from the sample"""
    _, _, samples, Z, Zn = clinic
    near, dist = screen_of(clinic).nearest(samples.copy(), k=K)
    expected = np.take_along_axis(cdist(Zn, Z), np.asarray(near), axis=1)
    assert np.allclose(dist, expected, rtol=1e-9, atol=0)


@pytest.mark.id("tst_qqmuh0")
def test_nearest_records(clinic):
    """The nearest records, nearest first"""
    _, _, samples, Z, Zn = clinic
    near, _ = screen_of(clinic).nearest(samples.copy(), k=K)
    expected = np.argsort(cdist(Zn, Z), axis=1, kind="stable")[:, :K]
    assert np.array_equal(near, expected)
