import numpy as np

PATH = "data/breast-cancer.csv"
# SciPy's bootstrap draws 9,999 resamples unless told otherwise, and the seed figures use.
REPEATS, SEED = 9999, 0


def clinic():
    """Whether the clinic's rule is right about each new sample, and the new samples' worst
    areas."""
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
    return (nearer == (new[:, 1] == 1)).astype(float), new[:, j]


def spread(values, statistic):
    """The standard deviation of statistic over REPEATS resamples of values."""
    rows = np.random.default_rng(SEED).integers(0, len(values), (REPEATS, len(values)))
    return np.std(statistic(values[rows], axis=-1), ddof=1)


def figures():
    right, area = clinic()
    n, p = len(right), right.mean()
    return {
        "right": str(int(right.sum())),
        "new": str(n),
        "accuracy": f"{p:.1%}",
        "repeats": f"{REPEATS:,}",
        "se": f"{spread(right, np.mean):.4f}",
        "formula": f"{np.sqrt(p * (1 - p) / n):.4f}",
        "left_out": f"{(1 - 1 / n) ** n:.1%}",
        "median_area": f"{np.median(area):,.1f}",
        "median_se": f"{spread(area, np.median):.1f}",
    }
