import numpy as np
import pytest

from evaluation import (
    basic_interval,
    percentile_interval,
    resample,
    resampled_accuracies,
)


@pytest.fixture(scope="module")
def clinic():
    """The clinic's rule's predictions for the new samples, and their diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    records, new = table[table[:, 0] == 0], table[table[:, 0] == 1]
    mean, std = records[:, 2:].mean(axis=0), records[:, 2:].std(axis=0)
    Z, Z_new = (records[:, 2:] - mean) / std, (new[:, 2:] - mean) / std
    malignant = Z[records[:, 1] == 1].mean(axis=0)
    benign = Z[records[:, 1] == 0].mean(axis=0)
    nearer = np.sum((Z_new - malignant) ** 2, axis=1) < np.sum(
        (Z_new - benign) ** 2, axis=1
    )
    return nearer.astype(float), new[:, 1]


@pytest.mark.id("tst_asoi7v")
def test_with_replacement():
    """Resamples that repeat some rows and leave others out"""
    rows = np.asarray(resample(114, 1000, np.random.default_rng(3)))
    distinct = np.mean([len(np.unique(row)) for row in rows])
    assert 0.6 * 114 < distinct < 0.67 * 114


@pytest.mark.id("tst_ps06xz")
def test_centered(clinic):
    """Resampled accuracies that center on the accuracy measured"""
    predictions, labels = clinic
    accuracies = resampled_accuracies(predictions, labels, 2000, 4)
    assert abs(np.mean(accuracies) - np.mean(predictions == labels)) < 0.01


@pytest.mark.id("tst_8eof09")
def test_levels():
    """A 95% interval that leaves 2.5% outside on each side"""
    accuracies = np.arange(1001) / 1000
    assert percentile_interval(accuracies, 0.95) == pytest.approx((0.025, 0.975))


@pytest.mark.id("tst_pclp9x")
def test_basic_in_order():
    """A basic interval from its low end to its high end"""
    accuracies = np.linspace(0.8, 0.95, 301)
    low, high = percentile_interval(accuracies, 0.95)
    found = basic_interval(0.9, accuracies, 0.95)
    assert found == pytest.approx((1.8 - high, 1.8 - low))
    assert found[0] < found[1]
