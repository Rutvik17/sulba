import numpy as np
from scipy.stats import norm, skew

PATH = "data/breast-cancer.csv"
# Resamples and seed for the clinic's intervals. The coverage comparison: samples drawn from
# the records, their size, the resamples of each, and the seed.
REPEATS, SEED = 9999, 0
SAMPLES, SIZE, SAMPLE_REPEATS, SAMPLE_SEED = 1000, 20, 999, 5


def clinic():
    """Whether the clinic's rule is right about each new sample, the new samples' worst areas,
    and the records' worst areas."""
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    with open(PATH) as file:
        j = file.readline().strip().split(",").index("worst_area")
    records, new = table[table[:, 0] == 0], table[table[:, 0] == 1]
    mean, std = records[:, 2:].mean(axis=0), records[:, 2:].std(axis=0)
    Z, Z_new = (records[:, 2:] - mean) / std, (new[:, 2:] - mean) / std
    malignant = Z[records[:, 1] == 1].mean(axis=0)
    benign = Z[records[:, 1] == 0].mean(axis=0)
    nearer = np.sum((Z_new - malignant) ** 2, axis=1) < np.sum(
        (Z_new - benign) ** 2, axis=1
    )
    return (nearer == (new[:, 1] == 1)).astype(float), new[:, j], records[:, j]


def corrections(values, distribution):
    """The bias correction z0 and the acceleration a, for the mean."""
    estimate = np.mean(values)
    below = np.sum(distribution < estimate) + np.sum(distribution <= estimate)
    n = len(values)
    left_out = np.tile(values, (n, 1))[~np.eye(n, dtype=bool)].reshape(n, n - 1)
    jackknife = np.mean(left_out, axis=-1)
    u = (n - 1) * (np.mean(jackknife) - jackknife)
    return norm.ppf(below / (2 * len(distribution))), np.sum(u**3) / (
        6 * np.sum(u**2) ** 1.5
    )


def intervals(values, distribution, confidence=0.95):
    """The percentile and BCa intervals, for the mean."""
    tail = (1 - confidence) / 2
    z0, a = corrections(values, distribution)
    z = norm.ppf(tail)
    levels = [norm.cdf(z0 + (z0 + end) / (1 - a * (z0 + end))) for end in (z, -z)]
    return np.quantile(distribution, [tail, 1 - tail]), np.quantile(
        distribution, levels
    )


def distribution(values, repeats, rng):
    """The mean over each of repeats resamples of values."""
    return np.mean(
        values[rng.integers(0, len(values), (repeats, len(values)))], axis=-1
    )


def figures():
    right, area, records = clinic()
    accuracy = distribution(right, REPEATS, np.random.default_rng(SEED))
    z0_right, a_right = corrections(right, accuracy)
    percentile_right, bca_right = intervals(right, accuracy)
    resampled = distribution(area, REPEATS, np.random.default_rng(SEED))
    z0, a = corrections(area, resampled)
    assert abs(a - skew(area) / (6 * np.sqrt(len(area)))) < 1e-12
    percentile, bca = intervals(area, resampled)
    rng = np.random.default_rng(SAMPLE_SEED)
    covered = np.zeros(2)
    for _ in range(SAMPLES):
        sample = records[rng.integers(0, len(records), SIZE)]
        found = distribution(sample, SAMPLE_REPEATS, rng)
        for k, (low, high) in enumerate(intervals(sample, found)):
            covered[k] += low <= records.mean() <= high
    covered /= SAMPLES
    assert covered[1] > covered[0]
    return {
        "accuracy": f"{right.mean():.1%}",
        "z0_right": f"{z0_right:.3f}",
        "a_right": f"{a_right:.3f}",
        "percentile_right_low": f"{percentile_right[0]:.1%}",
        "percentile_right_high": f"{percentile_right[1]:.1%}",
        "bca_right_low": f"{bca_right[0]:.1%}",
        "bca_right_high": f"{bca_right[1]:.1%}",
        "area_mean": f"{np.mean(area):,.1f}",
        "skew": f"{skew(area):.2f}",
        "z0": f"{z0:.3f}",
        "a": f"{a:.4f}",
        "percentile_low": f"{percentile[0]:,.1f}",
        "percentile_high": f"{percentile[1]:,.1f}",
        "bca_low": f"{bca[0]:,.1f}",
        "bca_high": f"{bca[1]:,.1f}",
        "samples": f"{SAMPLES:,}",
        "size": str(SIZE),
        "percentile_covered": f"{covered[0]:.1%}",
        "bca_covered": f"{covered[1]:.1%}",
    }
