from itertools import pairwise

import numpy as np
import pytest
from scipy.stats import bootstrap

from bootstrap import basic_interval, bootstrap_distribution, percentile_interval


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


def scipy_interval(values, method, repeats, seed):
    found = bootstrap(
        (values,),
        np.mean,
        n_resamples=repeats,
        method=method,
        rng=np.random.default_rng(seed),
    )
    return found.confidence_interval.low, found.confidence_interval.high


@pytest.mark.id("tst_l5wgzl")
def test_percentile_by_hand():
    """Percentile intervals worked by hand"""
    distribution = np.arange(101.0)
    assert percentile_interval(distribution, 0.95) == pytest.approx((2.5, 97.5))
    assert percentile_interval(distribution, 0.5) == pytest.approx((25, 75))


@pytest.mark.id("tst_7rdu45")
def test_percentile_like_scipy(clinic):
    """The same percentile intervals as SciPy's bootstrap"""
    for values, repeats, seed in ((clinic[0], 9999, 0), (clinic[1], 2000, 1)):
        distribution = bootstrap_distribution(
            values, np.mean, repeats, np.random.default_rng(seed)
        )
        expected = scipy_interval(values, "percentile", repeats, seed)
        assert percentile_interval(distribution, 0.95) == pytest.approx(
            expected, rel=1e-12
        )


@pytest.mark.id("tst_4xpedl")
def test_basic_by_hand():
    """Basic intervals worked by hand"""
    distribution = np.arange(101.0)
    assert basic_interval(60.0, distribution, 0.95) == pytest.approx((22.5, 117.5))
    assert basic_interval(50.0, distribution, 0.5) == pytest.approx((25, 75))


@pytest.mark.id("tst_4inbel")
def test_basic_like_scipy(clinic):
    """The same basic intervals as SciPy's bootstrap"""
    for values, repeats, seed in ((clinic[0], 9999, 0), (clinic[1], 2000, 1)):
        distribution = bootstrap_distribution(
            values, np.mean, repeats, np.random.default_rng(seed)
        )
        expected = scipy_interval(values, "basic", repeats, seed)
        found = basic_interval(np.mean(values), distribution, 0.95)
        assert found == pytest.approx(expected, rel=1e-12)


@pytest.mark.id("tst_u83p2l")
def test_wider_for_more_confidence(clinic):
    """A higher confidence gives a wider interval around the same one"""
    _, area = clinic
    distribution = bootstrap_distribution(area, np.mean, 2000, np.random.default_rng(2))
    intervals = [percentile_interval(distribution, c) for c in (0.8, 0.9, 0.95, 0.99)]
    for (low, high), (wider_low, wider_high) in pairwise(intervals):
        assert wider_low < low and high < wider_high
