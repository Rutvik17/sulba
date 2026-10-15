import numpy as np

from bootstrap import bootstrap_distribution, standard_error

SEED = 0


def chart(repeats):
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    records, new = table[table[:, 0] == 0], table[table[:, 0] == 1]
    mean, std = records[:, 2:].mean(axis=0), records[:, 2:].std(axis=0)
    Z, Z_new = (records[:, 2:] - mean) / std, (new[:, 2:] - mean) / std
    malignant = Z[records[:, 1] == 1].mean(axis=0)
    benign = Z[records[:, 1] == 0].mean(axis=0)
    nearer = np.sum((Z_new - malignant) ** 2, axis=1) < np.sum(
        (Z_new - benign) ** 2, axis=1
    )
    right = (nearer == (new[:, 1] == 1)).astype(float)
    n = len(right)
    found = np.asarray(
        bootstrap_distribution(right, np.mean, repeats, np.random.default_rng(SEED))
    )
    counts = np.bincount(np.rint(found * n).astype(int), minlength=n + 1)
    shown = np.arange(int(0.8 * n), n + 1)
    se = standard_error(found)
    return {
        "x": {"min": 0.8, "max": 1, "step": 0.05, "label": "accuracy on a resample"},
        "y": {"min": 0, "max": 0.25, "step": 0.05, "label": "share of resamples"},
        "lines": [
            {
                "style": "dashed",
                "label": "Accuracy measured",
                "x": [right.mean()] * 2,
                "y": [0, 0.25],
            },
            {
                "style": "main",
                "label": "Resamples",
                "x": shown / n,
                "y": counts[shown] / repeats,
            },
        ],
        "points": [],
        "readouts": [
            {"label": "Accuracy measured", "value": f"{right.mean():.1%}"},
            {"label": "Standard error", "value": f"{se:.4f}"},
            {"label": "Resamples", "value": f"{repeats:,}"},
        ],
        "description": (
            f"The share of {repeats:,} resamples of the clinic's {n} new samples on which its "
            f"rule reaches each accuracy, around the {right.mean():.1%} measured. Their "
            f"standard deviation, the standard error, is {se:.4f}."
        ),
    }
