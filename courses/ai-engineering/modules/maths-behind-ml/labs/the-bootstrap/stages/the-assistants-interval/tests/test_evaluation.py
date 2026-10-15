import numpy as np
import pytest

from evaluation import percentile_interval, resample, resampled_accuracies


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


@pytest.mark.id("tst_g034bc")
def test_resample_shape():
    """Resamples of repeats rows of n row numbers"""
    rows = np.asarray(resample(114, 50, np.random.default_rng(0)))
    assert rows.shape == (50, 114)
    assert rows.min() >= 0 and rows.max() <= 113


@pytest.mark.id("tst_yzyy9f")
def test_reproducible(clinic):
    """The same seed gives the same accuracies"""
    predictions, labels = clinic
    first = resampled_accuracies(predictions, labels, 200, 7)
    assert np.array_equal(first, resampled_accuracies(predictions, labels, 200, 7))


@pytest.mark.id("tst_37m51q")
def test_accuracies(clinic):
    """Accuracies between 0 and 1, one for each resample"""
    predictions, labels = clinic
    accuracies = np.asarray(resampled_accuracies(predictions, labels, 500, 1))
    assert accuracies.shape == (500,)
    assert accuracies.min() >= 0 and accuracies.max() <= 1


@pytest.mark.id("tst_5ydu0o")
def test_interval_inside(clinic):
    """The interval lies within the resampled accuracies"""
    predictions, labels = clinic
    accuracies = resampled_accuracies(predictions, labels, 500, 2)
    low, high = percentile_interval(accuracies, 0.95)
    assert np.min(accuracies) <= low <= high <= np.max(accuracies)
