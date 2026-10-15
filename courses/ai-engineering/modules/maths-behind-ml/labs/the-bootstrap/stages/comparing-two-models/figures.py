import numpy as np

PATH = "data/breast-cancer.csv"
# Resamples and seed for the clinic's intervals, and the checks' sizes.
REPEATS, SEED = 9999, 0
SYNTHETIC, MILLION, NEVER_N, NEVER_EXTRA = 1000, 1_000_000, 1000, 2


def rules():
    """Whether each of the clinic's rules is right about each new sample: the nearer class
    mean, and the nearest record."""
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
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


def points(value):
    """A difference in accuracy, in percentage points."""
    return f"{100 * value:.1f}".replace("-", "−")


def figures():
    right_a, right_b = rules()
    n = len(right_a)
    only_a, only_b = int(np.sum(right_a & ~right_b)), int(np.sum(right_b & ~right_a))
    rng = np.random.default_rng(SEED)
    counts = rng.multinomial(
        n, [only_a / n, only_b / n, (n - only_a - only_b) / n], size=REPEATS
    )
    paired = np.quantile((counts[:, 0] - counts[:, 1]) / n, [0.025, 0.975])
    rng = np.random.default_rng(SEED)
    apart = (
        rng.binomial(n, right_a.mean(), REPEATS) / n
        - rng.binomial(n, right_b.mean(), REPEATS) / n
    )
    unpaired = np.quantile(apart, [0.025, 0.975])
    return {
        "right": str(int(right_a.sum())),
        "right_b": str(int(right_b.sum())),
        "new": str(n),
        "disagree": str(only_a + only_b),
        "only_a": str(only_a),
        "only_b": str(only_b),
        "agree": str(n - only_a - only_b),
        "repeats": f"{REPEATS:,}",
        "low": points(paired[0]),
        "high": points(paired[1]),
        "unpaired_low": points(unpaired[0]),
        "unpaired_high": points(unpaired[1]),
        "synthetic": f"{SYNTHETIC:,}",
        "million": f"{MILLION:,}",
        "never_n": f"{NEVER_N:,}",
        "never_extra": str(NEVER_EXTRA),
    }
