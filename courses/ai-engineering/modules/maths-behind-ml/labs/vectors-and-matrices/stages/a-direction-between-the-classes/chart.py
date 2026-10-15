import numpy as np

from vectors import centroids, scores

# Bins one standard deviation wide, covering every new sample's score.
EDGES = np.arange(-7, 11)


def chart(threshold):
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X, y = table[~new, 2:], table[~new, 1]
    mean, std = X.mean(axis=0), X.std(axis=0)
    mu0, mu1 = centroids((X - mean) / std, y)
    score = np.asarray(scores((table[new, 2:] - mean) / std, mu0, mu1), dtype=float)
    malignant = table[new, 1] == 1
    centres = (EDGES[:-1] + EDGES[1:]) / 2
    above_malignant = int(np.sum(score[malignant] >= threshold))
    above_benign = int(np.sum(score[~malignant] >= threshold))
    return {
        "x": {
            "min": -7,
            "max": 10,
            "step": 1,
            "label": "score, in standard deviations",
        },
        "y": {"min": 0, "max": 20, "step": 5, "label": "new samples"},
        "lines": [
            {
                "style": "dashed",
                "label": "Threshold",
                "x": [threshold, threshold],
                "y": [0, 20],
            },
            {
                "style": "base",
                "label": "Benign samples",
                "x": centres,
                "y": np.histogram(score[~malignant], EDGES)[0],
            },
            {
                "style": "main",
                "label": "Malignant samples",
                "x": centres,
                "y": np.histogram(score[malignant], EDGES)[0],
            },
        ],
        "points": [],
        "readouts": [
            {
                "label": "Malignant samples at or above it",
                "value": f"{above_malignant} of {int(malignant.sum())}",
            },
            {
                "label": "Benign samples at or above it",
                "value": f"{above_benign} of {int((~malignant).sum())}",
            },
        ],
        "description": (
            f"How many of the {len(score)} new samples score in each range, malignant and "
            f"benign. At a threshold of {threshold:g}, {above_malignant} of the "
            f"{int(malignant.sum())} malignant samples and {above_benign} of the "
            f"{int((~malignant).sum())} benign ones score at or above it."
        ),
    }
