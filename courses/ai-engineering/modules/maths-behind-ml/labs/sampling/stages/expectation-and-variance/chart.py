import numpy as np

from sampling import batch_mean_variance, simulated_means

# The batch sizes simulated, and how many batches each.
SIMULATED, REPEATS = (8, 32, 128, 300), 2000


def chart():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    y = table[table[:, 0] == 0, 1]
    n = len(y)
    sizes = np.arange(1, n + 1)
    without = np.sqrt([batch_mean_variance(y, int(b)) for b in sizes])
    rng = np.random.default_rng(0)
    simulated = [float(np.std(simulated_means(y, b, rng, REPEATS))) for b in SIMULATED]
    at32 = float(np.sqrt(batch_mean_variance(y, 32)))
    at32_with = float(np.std(y) / np.sqrt(32))
    return {
        "x": {"min": 0, "max": 500, "step": 50, "label": "batch size"},
        "y": {
            "min": 0,
            "max": 0.5,
            "step": 0.1,
            "label": "standard deviation of the share",
        },
        "lines": [
            {
                "style": "base",
                "label": "Drawn with replacement",
                "x": sizes,
                "y": np.std(y) / np.sqrt(sizes),
            },
            {
                "style": "main",
                "label": "Drawn without replacement",
                "x": sizes,
                "y": without,
            },
        ],
        "points": [{"x": b, "y": s} for b, s in zip(SIMULATED, simulated, strict=True)],
        "readouts": [
            {"label": "Batches of 32, without replacement", "value": f"{at32:.4f}"},
            {"label": "Batches of 32, with replacement", "value": f"{at32_with:.4f}"},
            {
                "label": f"{REPEATS:,} simulated batches of 32",
                "value": f"{simulated[1]:.4f}",
            },
        ],
        "description": (
            "How far a batch's share of malignant records strays from the records' share, as "
            "a standard deviation, for every batch size, drawn without replacement and with "
            f"it. For batches of 32 it is {at32:.4f}, and {simulated[1]:.4f} over "
            f"{REPEATS:,} simulated batches."
        ),
    }
