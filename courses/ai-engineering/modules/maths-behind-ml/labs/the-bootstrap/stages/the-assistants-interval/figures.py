import numpy as np

PATH = "data/breast-cancer.csv"
# The resamples, seed and confidence the clinic's interval uses.
REPEATS, SEED, CONFIDENCE = 9999, 0, 0.95


def clinic():
    """The clinic's rule's predictions for the new samples, and their diagnoses."""
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    records, new = table[table[:, 0] == 0], table[table[:, 0] == 1]
    mean, std = records[:, 2:].mean(axis=0), records[:, 2:].std(axis=0)
    Z, Z_new = (records[:, 2:] - mean) / std, (new[:, 2:] - mean) / std
    malignant = Z[records[:, 1] == 1].mean(axis=0)
    benign = Z[records[:, 1] == 0].mean(axis=0)
    nearer = np.sum((Z_new - malignant) ** 2, axis=1) < np.sum(
        (Z_new - benign) ** 2, axis=1
    )
    return nearer.astype(float), new[:, 1]


def quantiles(accuracies, levels):
    return np.quantile(accuracies, levels)


def figures():
    predictions, labels = clinic()
    n = len(labels)
    accuracy = np.mean(predictions == labels)
    rows = np.random.default_rng(SEED).integers(0, n, (REPEATS, n))
    right = np.mean(predictions[rows] == labels[rows], axis=1)
    unpaired = np.mean(predictions[rows] == labels, axis=1)
    tail = (1 - CONFIDENCE) / 2
    low, high = quantiles(right, [tail, 1 - tail])
    narrow_low, narrow_high = quantiles(right, [1 - CONFIDENCE, CONFIDENCE])
    unpaired_low, unpaired_high = quantiles(unpaired, [tail, 1 - tail])
    said, malignant = predictions.mean(), labels.mean()
    return {
        "new": str(n),
        "level": f"{CONFIDENCE:.0%}",
        "narrow_level": f"{2 * CONFIDENCE - 1:.0%}",
        "accuracy": f"{accuracy:.1%}",
        "unpaired_mean": f"{unpaired.mean():.1%}",
        "chance": f"{said * malignant + (1 - said) * (1 - malignant):.1%}",
        "said": f"{said:.1%}",
        "malignant": f"{malignant:.1%}",
        "unpaired_low": f"{unpaired_low:.1%}",
        "unpaired_high": f"{unpaired_high:.1%}",
        "low": f"{low:.1%}",
        "high": f"{high:.1%}",
        "narrow_low": f"{narrow_low:.1%}",
        "narrow_high": f"{narrow_high:.1%}",
        "basic_low": f"{2 * accuracy - high:.1%}",
        "basic_high": f"{2 * accuracy - low:.1%}",
    }
