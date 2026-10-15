import numpy as np

from similar import (
    column_stats,
    distances,
    malignant_share,
    nearest,
    split,
    standardize,
)


def chart(k):
    k = int(k)
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    records, diagnoses, new, own = split(table)
    mean, std = column_stats(records)
    D = distances(standardize(new, mean, std), standardize(records, mean, std))
    share = np.asarray(malignant_share(nearest(D, k), diagnoses), dtype=float)
    # Shares can only be whole numbers of records out of k.
    counts = np.rint(share * k).astype(int)
    steps = np.arange(k + 1)
    malignant = own == 1
    in_malignant = np.bincount(counts[malignant], minlength=k + 1)
    in_benign = np.bincount(counts[~malignant], minlength=k + 1)
    mostly_malignant = int(np.sum(share[malignant] > 0.5))
    mostly_benign = int(np.sum(share[~malignant] < 0.5))
    records_word = "record" if k == 1 else f"{k} records"
    return {
        "x": {
            "min": 0,
            "max": 1,
            "step": 0.2,
            "label": f"share of malignant records among the nearest {k}",
        },
        "y": {"min": 0, "max": 80, "step": 10, "label": "new samples"},
        "lines": [
            {
                "style": "base",
                "label": "Benign samples",
                "x": steps / k,
                "y": in_benign,
            },
            {
                "style": "main",
                "label": "Malignant samples",
                "x": steps / k,
                "y": in_malignant,
            },
        ],
        "points": [],
        "readouts": [
            {
                "label": "Malignant samples, mostly malignant records",
                "value": f"{mostly_malignant} of {int(malignant.sum())}",
            },
            {
                "label": "Benign samples, mostly benign records",
                "value": f"{mostly_benign} of {int((~malignant).sum())}",
            },
        ],
        "description": (
            f"For each of the {len(new)} new samples, the share of malignant records among "
            f"its nearest {records_word}: {mostly_malignant} of the {int(malignant.sum())} "
            f"malignant samples have mostly malignant records, and {mostly_benign} of the "
            f"{int((~malignant).sum())} benign samples mostly benign ones."
        ),
    }
