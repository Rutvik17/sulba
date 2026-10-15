import numpy as np

from bootstrap import bca_interval, bootstrap_distribution, percentile_interval

# Resamples of the new samples, their seed, and the histogram's bins.
REPEATS, SEED = 9999, 0
EDGES = np.arange(700.0, 1101.0, 10.0)


def chart(confidence):
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    with open("data/breast-cancer.csv") as file:
        j = file.readline().strip().split(",").index("worst_area")
    area = table[table[:, 0] == 1, j]
    found = np.asarray(
        bootstrap_distribution(area, np.mean, REPEATS, np.random.default_rng(SEED))
    )
    counts, _ = np.histogram(found, EDGES)
    shares = counts / REPEATS
    top = 0.1
    percentile = percentile_interval(found, confidence)
    bca = bca_interval(area, np.mean, found, confidence)

    def ends(low, high):
        """Two upright lines at an interval's ends, broken between them."""
        return [low, low, (low + high) / 2, high, high], [0, top, None, 0, top]

    middles = (EDGES[:-1] + EDGES[1:]) / 2
    percentile_x, percentile_y = ends(*percentile)
    bca_x, bca_y = ends(*bca)
    return {
        "x": {
            "min": 700,
            "max": 1100,
            "step": 50,
            "label": "mean worst area of a resample",
        },
        "y": {"min": 0, "max": top, "step": 0.02, "label": "share of resamples"},
        "lines": [
            {"style": "faint", "label": "Resamples", "x": middles, "y": shares},
            {
                "style": "dashed",
                "label": "Percentile interval",
                "x": percentile_x,
                "y": percentile_y,
            },
            {"style": "main", "label": "BCa interval", "x": bca_x, "y": bca_y},
        ],
        "points": [],
        "readouts": [
            {"label": "Mean worst area", "value": f"{np.mean(area):,.1f}"},
            {
                "label": "Percentile interval",
                "value": f"{percentile[0]:,.1f} to {percentile[1]:,.1f}",
            },
            {"label": "BCa interval", "value": f"{bca[0]:,.1f} to {bca[1]:,.1f}"},
        ],
        "description": (
            f"The mean worst area of each of {REPEATS:,} resamples of the clinic's "
            f"{len(area)} new samples, whose own mean is {np.mean(area):,.1f}, with the "
            f"{confidence:.0%} percentile interval, {percentile[0]:,.1f} to {percentile[1]:,.1f}, "
            f"and the BCa interval, {bca[0]:,.1f} to {bca[1]:,.1f}."
        ),
    }
