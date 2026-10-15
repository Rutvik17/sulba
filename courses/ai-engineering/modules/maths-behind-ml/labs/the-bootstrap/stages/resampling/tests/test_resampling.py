import numpy as np
import pytest
from scipy.stats import bootstrap

from bootstrap import bootstrap_distribution, resample, standard_error


@pytest.fixture(scope="module")
def clinic():
    """Whether the clinic's rule is right about each new sample, and the new samples' worst
    areas. The rule calls a sample malignant when it is nearer the malignant records' mean
    than the benign ones', with each measurement standardized."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    with open("data/breast-cancer.csv") as file:
        j = file.readline().strip().split(",").index("worst_area")
    records, new = table[table[:, 0] == 0], table[table[:, 0] == 1]
    mean, std = records[:, 2:].mean(axis=0), records[:, 2:].std(axis=0)
    Z, Z_new = (records[:, 2:] - mean) / std, (new[:, 2:] - mean) / std
    malignant = Z[records[:, 1] == 1].mean(axis=0)
    benign = Z[records[:, 1] == 0].mean(axis=0)
    nearer = np.sum((Z_new - malignant) ** 2, axis=1) < np.sum(
        (Z_new - benign) ** 2, axis=1
    )
    return (nearer == (new[:, 1] == 1)).astype(float), new[:, j]


@pytest.mark.id("tst_e541ad")
def test_resample():
    """Resamples of repeats rows of n row numbers, drawn with replacement"""
    rows = np.asarray(resample(114, 1000, np.random.default_rng(0)))
    assert rows.shape == (1000, 114)
    assert rows.min() >= 0 and rows.max() <= 113
    distinct = np.mean([len(np.unique(row)) for row in rows])
    assert 0.6 * 114 < distinct < 0.67 * 114


@pytest.mark.id("tst_ipix4x")
def test_accuracy_like_scipy(clinic):
    """The same distribution as SciPy's bootstrap, for the clinic's accuracy"""
    right, _ = clinic
    found = bootstrap_distribution(right, np.mean, 9999, np.random.default_rng(0))
    scipy = bootstrap((right,), np.mean, n_resamples=9999, rng=np.random.default_rng(0))
    assert np.array_equal(np.asarray(found), scipy.bootstrap_distribution)


@pytest.mark.id("tst_n0bi21")
def test_median_like_scipy(clinic):
    """The same distribution as SciPy's bootstrap, for the median worst area"""
    _, area = clinic
    found = bootstrap_distribution(area, np.median, 2000, np.random.default_rng(1))
    scipy = bootstrap(
        (area,), np.median, n_resamples=2000, rng=np.random.default_rng(1)
    )
    assert np.array_equal(np.asarray(found), scipy.bootstrap_distribution)


@pytest.mark.id("tst_gpg2ma")
def test_standard_error_like_scipy(clinic):
    """The same standard error as SciPy's bootstrap"""
    _, area = clinic
    scipy = bootstrap((area,), np.mean, n_resamples=2000, rng=np.random.default_rng(2))
    found = standard_error(scipy.bootstrap_distribution)
    assert found == pytest.approx(scipy.standard_error, rel=1e-12)
    assert standard_error(np.array([1.0, 2.0, 3.0, 4.0])) == pytest.approx(
        np.sqrt(5 / 3)
    )


@pytest.mark.id("tst_zsimfd")
def test_share_formula(clinic):
    """The accuracy's standard error, close to the formula for a share"""
    right, _ = clinic
    p, n = right.mean(), len(right)
    found = standard_error(
        bootstrap_distribution(right, np.mean, 9999, np.random.default_rng(3))
    )
    assert found == pytest.approx(np.sqrt(p * (1 - p) / n), rel=0.03)
