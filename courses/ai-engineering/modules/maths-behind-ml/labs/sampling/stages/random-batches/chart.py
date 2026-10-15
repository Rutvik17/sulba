import numpy as np

from sampling import batch_mean, shuffled_batches

SEED = 0


def chart(size):
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    y = table[table[:, 0] == 0, 1]
    n = len(y)
    batches = shuffled_batches(n, size, np.random.default_rng(SEED))
    ends = np.cumsum([len(batch) for batch in batches])
    middles = ends - np.array([len(batch) for batch in batches]) / 2
    shares = np.array([float(batch_mean(y, batch)) for batch in batches])
    return {
        "x": {"min": 0, "max": 500, "step": 50, "label": "records into the epoch"},
        "y": {"min": 0, "max": 1, "step": 0.25, "label": "share malignant"},
        "lines": [
            {
                "style": "dashed",
                "label": "All the records",
                "x": [0, n],
                "y": [y.mean()] * 2,
            },
            {"style": "main", "label": "Each batch", "x": middles, "y": shares},
        ],
        "points": [
            {"x": float(x), "y": float(s)} for x, s in zip(middles, shares, strict=True)
        ],
        "readouts": [
            {"label": "Batches", "value": str(len(batches))},
            {"label": "Lowest share", "value": f"{shares.min():.1%}"},
            {"label": "Highest share", "value": f"{shares.max():.1%}"},
        ],
        "description": (
            f"The share of malignant records in each of the {len(batches)} batches of one "
            f"shuffled epoch, with batches of {size}. It runs from {shares.min():.1%} to "
            f"{shares.max():.1%}, around {y.mean():.1%} for all the records."
        ),
    }
