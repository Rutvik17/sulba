import time

import numpy as np
import pytest
from scipy.stats import bootstrap

from bootstrap import paired_difference

# The samples and resamples the speed check uses, its limit, and the random numbers a
# comparison may draw for each resample on a small input before it counts as resampling
# every sample.
MILLION, REPEATS, LIMIT_S, PER_RESAMPLE = 1_000_000, 9999, 1.0, 100


@pytest.fixture(scope="module")
def rules():
    """Whether each of the clinic's rules is right about each new sample: the nearer class
    mean, and the nearest record."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    records, new = table[table[:, 0] == 0], table[table[:, 0] == 1]
    mean, std = records[:, 2:].mean(axis=0), records[:, 2:].std(axis=0)
    Z, Z_new = (records[:, 2:] - mean) / std, (new[:, 2:] - mean) / std
    malignant = Z[records[:, 1] == 1].mean(axis=0)
    benign = Z[records[:, 1] == 0].mean(axis=0)
    nearer = np.sum((Z_new - malignant) ** 2, axis=1) < np.sum(
        (Z_new - benign) ** 2, axis=1
    )
    distances = np.sum((Z_new[:, None, :] - Z[None, :, :]) ** 2, axis=2)
    nearest = records[np.argmin(distances, axis=1), 1] == 1
    labels = new[:, 1] == 1
    return nearer == labels, nearest == labels


def models(n, seed):
    """Two models' results on n samples: the first right on about 85%, the second disagreeing
    with it on about 9%."""
    rng = np.random.default_rng(seed)
    right_a = rng.random(n) < 0.85
    return right_a, np.where(rng.random(n) < 0.09, ~right_a, right_a)


class Counted:
    """Stands in for a generator, adding up how many random numbers each call draws."""

    def __init__(self, rng):
        self.rng, self.drawn = rng, 0

    def __getattr__(self, name):
        method = getattr(self.rng, name)

        def counted(*args, **kwargs):
            found = method(*args, **kwargs)
            self.drawn += np.size(args[0]) if found is None else np.size(found)
            return found

        return counted


@pytest.mark.id("tst_fvcatb")
def test_like_resampling(rules):
    """The same intervals as resampling the samples"""

    def difference(a, b, axis=-1):
        return np.mean(a, axis=axis) - np.mean(b, axis=axis)

    for (right_a, right_b), tolerance in ((rules, 1.5 / 114), (models(1000, 5), 0.004)):
        expected = bootstrap(
            (right_a.astype(float), right_b.astype(float)),
            difference,
            paired=True,
            method="percentile",
            n_resamples=4999,
            rng=np.random.default_rng(6),
        ).confidence_interval
        found = paired_difference(
            right_a, right_b, 0.95, REPEATS, np.random.default_rng(7)
        )
        assert found == pytest.approx((expected.low, expected.high), abs=tolerance)


@pytest.mark.id("tst_rlnvyp")
def test_against_itself(rules):
    """A model against itself"""
    for right in (rules[0], models(2000, 8)[0]):
        assert paired_difference(
            right, right, 0.95, REPEATS, np.random.default_rng(9)
        ) == (0, 0)


@pytest.mark.id("tst_oya800")
def test_never_worse(record_property):
    """A model never worse"""
    right_a = np.arange(1000) < 900
    right_b = right_a & (np.arange(1000) >= 2)
    low, _ = paired_difference(
        right_a, right_b, 0.95, REPEATS, np.random.default_rng(16)
    )
    if low < 0:
        record_property("note", f"The interval starts at {low:.4f}")
        pytest.fail("It put model b ahead, which no resample can.")


@pytest.mark.id("tst_lqa74p")
def test_fast(record_property):
    """Fast on a million samples"""
    right_a, right_b = models(2000, 10)
    rng = Counted(np.random.default_rng(11))
    paired_difference(right_a, right_b, 0.95, 999, rng)
    if rng.drawn > PER_RESAMPLE * 999:
        record_property(
            "note",
            f"{rng.drawn:,} random numbers for 2,000 samples and 999 resamples, so about "
            f"{rng.drawn * (MILLION // 2000) * (REPEATS / 999):,.0f} for a million samples "
            f"and {REPEATS:,} resamples",
        )
        pytest.fail("It draws random numbers for every sample of every resample.")
    right_a, right_b = models(MILLION, 12)
    start = time.perf_counter()
    paired_difference(right_a, right_b, 0.95, REPEATS, np.random.default_rng(13))
    took = time.perf_counter() - start
    record_property("note", f"{took:.3f} seconds for {MILLION:,} samples")
    assert took < LIMIT_S


@pytest.mark.id("tst_fxlxiq")
def test_different_samples(record_property):
    """Refuses results from different samples"""
    right_a, right_b = models(2000, 14)
    try:
        found = paired_difference(
            right_a, right_b[:-1], 0.95, 999, np.random.default_rng(15)
        )
    except ValueError:
        return
    record_property("note", f"It gave {found} for 2,000 results against 1,999")
    pytest.fail("It compared results from different samples.")
