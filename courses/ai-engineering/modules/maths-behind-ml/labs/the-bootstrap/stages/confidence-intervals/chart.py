import numpy as np

from bootstrap import basic_interval, bootstrap_distribution, percentile_interval

# The sample sizes tried, the samples drawn at each size, and the resamples of each sample.
SIZES, SAMPLES, REPEATS = (10, 20, 40, 80), 150, 499


def chart():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    with open("data/breast-cancer.csv") as file:
        j = file.readline().strip().split(",").index("worst_area")
    area = table[table[:, 0] == 0, j]
    truth = area.mean()
    rng = np.random.default_rng(0)
    covered = np.zeros((2, len(SIZES)))
    for k, n in enumerate(SIZES):
        for _ in range(SAMPLES):
            sample = area[rng.integers(0, len(area), n)]
            distribution = bootstrap_distribution(sample, np.mean, REPEATS, rng)
            percentile = percentile_interval(distribution, 0.95)
            basic = basic_interval(np.mean(sample), distribution, 0.95)
            for row, (low, high) in enumerate((percentile, basic)):
                covered[row, k] += low <= truth <= high
    covered /= SAMPLES
    return {
        "x": {"min": 0, "max": 80, "step": 10, "label": "samples drawn"},
        "y": {
            "min": 0.7,
            "max": 1,
            "step": 0.05,
            "label": "share of intervals covering the mean",
        },
        "lines": [
            {"style": "dashed", "label": "95%", "x": [0, 80], "y": [0.95, 0.95]},
            {"style": "base", "label": "Basic intervals", "x": SIZES, "y": covered[1]},
            {
                "style": "main",
                "label": "Percentile intervals",
                "x": SIZES,
                "y": covered[0],
            },
        ],
        "points": [
            {"x": n, "y": float(c)} for n, c in zip(SIZES, covered[0], strict=True)
        ],
        "readouts": [
            {
                "label": f"Percentile, {SIZES[0]} samples",
                "value": f"{covered[0, 0]:.1%}",
            },
            {
                "label": f"Percentile, {SIZES[-1]} samples",
                "value": f"{covered[0, -1]:.1%}",
            },
            {"label": f"Basic, {SIZES[0]} samples", "value": f"{covered[1, 0]:.1%}"},
            {"label": f"Basic, {SIZES[-1]} samples", "value": f"{covered[1, -1]:.1%}"},
        ],
        "description": (
            f"The share of {SAMPLES} samples from the clinic's records, at each size, whose 95% "
            "interval for the mean worst area covers the records' mean: "
            f"{covered[0, 0]:.1%} for percentile intervals and {covered[1, 0]:.1%} for basic "
            f"ones at {SIZES[0]} samples, and {covered[0, -1]:.1%} and {covered[1, -1]:.1%} at "
            f"{SIZES[-1]}."
        ),
    }
