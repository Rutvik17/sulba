import numpy as np

from network import network
from range_test import lowest, range_test

# The office's network from its start, on BATCHES batches of BATCH training digits, at
# learning rates rising from LR_MIN to LR_MAX.
BATCHES, BATCH, LR_MIN, LR_MAX, TOP = 300, 64, 1e-3, 10.0, 3.0


def chart(beta):
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    X, digits, sets = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]
    rng = np.random.default_rng(0)
    params = network(rng)
    training = np.flatnonzero(sets == 0)
    batches = []
    for _ in range(BATCHES):
        rows = rng.choice(training, size=BATCH, replace=False)
        batches.append((X[rows], digits[rows]))
    lrs, smoothed = range_test(params, batches, LR_MIN, LR_MAX, beta=beta)
    return {
        "x": {"min": -3, "max": 1, "step": 0.5, "label": "learning rate, as a power of 10"},
        "y": {"min": 0, "max": TOP, "step": 0.5, "label": "smoothed loss"},
        "lines": [
            {
                "style": "main",
                "label": "Your range test",
                "x": np.log10(lrs),
                "y": [float(v) if np.isfinite(v) and v <= TOP else None for v in smoothed],
            }
        ],
        "points": [],
        "readouts": [
            {"label": "Lowest smoothed loss", "value": f"{np.min(smoothed):.2f}"},
            {"label": "At a learning rate of", "value": f"{lowest(lrs, smoothed):.3g}"},
        ],
        "description": (
            f"The smoothed loss of the office's network over {len(lrs)} steps, at learning "
            f"rates rising from {LR_MIN:g} to {lrs[-1]:.3g}, averaged with beta {beta:g}"
        ),
    }
