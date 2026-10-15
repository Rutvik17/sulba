import numpy as np

from vectors import centroids, cosine, norm


def chart():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    in_records = table[:, 0] == 0
    X, y = table[in_records, 2:], table[in_records, 1]
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    mu0, mu1 = (np.asarray(mean, dtype=float) for mean in centroids(Z, y))
    number = np.arange(1, Z.shape[1] + 1)
    angle = cosine(mu0, mu1)
    return {
        "x": {
            "min": 0,
            "max": Z.shape[1],
            "step": 5,
            "label": "measurement, in the data's order",
        },
        "y": {
            "min": -1.2,
            "max": 1.2,
            "step": 0.4,
            "label": "mean, in standard deviations",
        },
        "lines": [
            {
                "style": "dashed",
                "label": "All records",
                "x": [0, Z.shape[1]],
                "y": [0, 0],
            },
            {"style": "base", "label": "Average benign record", "x": number, "y": mu0},
            {
                "style": "main",
                "label": "Average malignant record",
                "x": number,
                "y": mu1,
            },
        ],
        "points": [],
        "readouts": [
            {"label": "Length of the malignant mean", "value": f"{norm(mu1):.2f}"},
            {"label": "Length of the benign mean", "value": f"{norm(mu0):.2f}"},
            {"label": "Cosine between them", "value": f"{angle:.3f}"},
        ],
        "description": (
            f"The average malignant and average benign record, measurement by measurement, "
            f"in standard deviations from the records' mean. Their lengths are "
            f"{norm(mu1):.2f} and {norm(mu0):.2f}, and the cosine between them is "
            f"{angle:.3f}."
        ),
    }
