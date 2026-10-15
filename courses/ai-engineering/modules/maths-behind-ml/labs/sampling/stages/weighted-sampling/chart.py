import numpy as np

from sampling import balanced_weights, reweighted_mean, weighted_choice

# Batches of SIZE records, and how many are drawn with each set of weights.
SIZE, BATCHES = 32, 4000


def chart():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    y = table[table[:, 0] == 0, 1]
    n = len(y)
    rng = np.random.default_rng(0)
    weights = np.asarray(balanced_weights(y))
    equal = np.asarray(weighted_choice(np.ones(n), SIZE * BATCHES, rng)).reshape(
        BATCHES, SIZE
    )
    balanced = np.asarray(weighted_choice(weights, SIZE * BATCHES, rng)).reshape(
        BATCHES, SIZE
    )
    counts = np.arange(SIZE + 1)

    def shares(batches):
        """The share of batches that hold each number of malignant records."""
        found = y[batches].sum(axis=1).astype(int)
        return np.bincount(found, minlength=SIZE + 1) / len(batches)

    plain = float(y[equal].sum(axis=1).mean())
    weighted = float(y[balanced].sum(axis=1).mean())
    reweighted = float(
        np.mean([reweighted_mean(y, batch, weights) for batch in balanced])
    )
    return {
        "x": {
            "min": 0,
            "max": SIZE,
            "step": 4,
            "label": f"malignant records in a batch of {SIZE}",
        },
        "y": {"min": 0, "max": 0.2, "step": 0.05, "label": "share of batches"},
        "lines": [
            {
                "style": "base",
                "label": "Equal weights",
                "x": counts,
                "y": shares(equal),
            },
            {
                "style": "main",
                "label": "Balanced weights",
                "x": counts,
                "y": shares(balanced),
            },
        ],
        "points": [],
        "readouts": [
            {"label": "Equal weights, malignant per batch", "value": f"{plain:.1f}"},
            {
                "label": "Balanced weights, malignant per batch",
                "value": f"{weighted:.1f}",
            },
            {
                "label": "Balanced weights, reweighted share",
                "value": f"{reweighted:.1%}",
            },
            {"label": "All the records, share malignant", "value": f"{y.mean():.1%}"},
        ],
        "description": (
            f"How many malignant records each of {BATCHES:,} batches of {SIZE} holds, drawn "
            f"with equal weights and with balanced ones: {plain:.1f} on average with equal "
            f"weights and {weighted:.1f} with balanced ones, whose reweighted share malignant "
            f"averages {reweighted:.1%}, against {y.mean():.1%} for all the records."
        ),
    }
