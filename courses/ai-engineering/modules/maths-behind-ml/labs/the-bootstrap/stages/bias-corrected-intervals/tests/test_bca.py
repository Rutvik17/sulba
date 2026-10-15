import numpy as np
import pytest
from scipy.stats import bootstrap

from bootstrap import bca_interval, bootstrap_distribution, percentile_interval


@pytest.fixture(scope="module")
def clinic():
    """Whether the clinic's rule is right about each new sample, and the new samples' worst
    areas."""
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


def both(values, statistic, repeats, seed, confidence=0.95):
    """Your BCa interval and SciPy's, from the same resamples."""
    distribution = bootstrap_distribution(
        values, statistic, repeats, np.random.default_rng(seed)
    )
    found = bca_interval(values, statistic, distribution, confidence)
    scipy = bootstrap(
        (values,),
        statistic,
        n_resamples=repeats,
        confidence_level=confidence,
        rng=np.random.default_rng(seed),
    ).confidence_interval
    return found, (scipy.low, scipy.high)


@pytest.mark.id("tst_bcw8zp")
def test_accuracy_like_scipy(clinic):
    """The same BCa interval as SciPy's, for the clinic's accuracy"""
    found, expected = both(clinic[0], np.mean, 9999, 0)
    assert found == pytest.approx(expected, rel=1e-9)


@pytest.mark.id("tst_lc9v4c")
def test_mean_like_scipy(clinic):
    """The same BCa interval as SciPy's, for the mean worst area"""
    found, expected = both(clinic[1], np.mean, 2000, 1)
    assert found == pytest.approx(expected, rel=1e-9)


@pytest.mark.id("tst_nmk4v7")
def test_median_like_scipy(clinic):
    """The same BCa interval as SciPy's, for the median worst area"""
    found, expected = both(clinic[1], np.median, 2000, 2)
    assert found == pytest.approx(expected, rel=1e-9)


@pytest.mark.id("tst_s0yt5q")
def test_other_confidence(clinic):
    """The same BCa interval as SciPy's at 90% and 99% confidence"""
    for confidence in (0.9, 0.99):
        found, expected = both(clinic[1], np.mean, 2000, 3, confidence)
        assert found == pytest.approx(expected, rel=1e-9)


@pytest.mark.id("tst_f8vdep")
def test_toward_the_tail(clinic):
    """For the skewed worst area, both ends above the percentile interval's"""
    _, area = clinic
    distribution = bootstrap_distribution(area, np.mean, 2000, np.random.default_rng(4))
    low, high = bca_interval(area, np.mean, distribution, 0.95)
    percentile_low, percentile_high = percentile_interval(distribution, 0.95)
    assert low > percentile_low and high > percentile_high
