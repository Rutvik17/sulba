import numpy as np
from scipy.stats import skew

PATH = "data/breast-cancer.csv"
# The clinic's interval: 9,999 resamples and their seed. The chart's sample sizes, samples
# drawn at each size, and resamples of each sample.
REPEATS, SEED = 9999, 0
SIZES, SAMPLES, CHART_REPEATS = (10, 20, 40, 80), 150, 499


def clinic():
    """Whether the clinic's rule is right about each new sample."""
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    records, new = table[table[:, 0] == 0], table[table[:, 0] == 1]
    mean, std = records[:, 2:].mean(axis=0), records[:, 2:].std(axis=0)
    Z, Z_new = (records[:, 2:] - mean) / std, (new[:, 2:] - mean) / std
    malignant = Z[records[:, 1] == 1].mean(axis=0)
    benign = Z[records[:, 1] == 0].mean(axis=0)
    nearer = np.sum((Z_new - malignant) ** 2, axis=1) < np.sum(
        (Z_new - benign) ** 2, axis=1
    )
    return (nearer == (new[:, 1] == 1)).astype(float)


def interval(distribution, confidence=0.95):
    tail = (1 - confidence) / 2
    return np.quantile(distribution, [tail, 1 - tail])


def coverage(area):
    """The chart's shares of samples whose percentile and basic intervals cover the mean."""
    rng = np.random.default_rng(0)
    covered = np.zeros((2, len(SIZES)))
    for k, n in enumerate(SIZES):
        for _ in range(SAMPLES):
            sample = area[rng.integers(0, len(area), n)]
            rows = rng.integers(0, n, (CHART_REPEATS, n))
            low, high = interval(np.mean(sample[rows], axis=-1))
            estimate = np.mean(sample)
            covered[0, k] += low <= area.mean() <= high
            covered[1, k] += 2 * estimate - high <= area.mean() <= 2 * estimate - low
    return covered / SAMPLES


def figures():
    right = clinic()
    rows = np.random.default_rng(SEED).integers(0, len(right), (REPEATS, len(right)))
    low, high = interval(np.mean(right[rows], axis=-1))
    p = right.mean()
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    with open(PATH) as file:
        j = file.readline().strip().split(",").index("worst_area")
    area = table[table[:, 0] == 0, j]
    covered = coverage(area)
    return {
        "accuracy": f"{p:.1%}",
        "low": f"{low:.1%}",
        "high": f"{high:.1%}",
        "basic_low": f"{2 * p - high:.1%}",
        "basic_high": f"{2 * p - low:.1%}",
        "below": f"{100 * (p - low):.1f}",
        "above": f"{100 * (high - p):.1f}",
        "records": str(len(area)),
        "area_mean": f"{area.mean():,.1f}",
        "area_median": f"{np.median(area):,.1f}",
        "area_max": f"{area.max():,.0f}",
        "skew": f"{skew(area):.2f}",
        "samples": str(SAMPLES),
        "few": str(SIZES[0]),
        "many": str(SIZES[-1]),
        "percentile_few": f"{covered[0, 0]:.1%}",
        "percentile_many": f"{covered[0, -1]:.1%}",
        "basic_few": f"{covered[1, 0]:.1%}",
        "basic_many": f"{covered[1, -1]:.1%}",
    }
