import numpy as np
from scipy.spatial.distance import cdist

from gradients import numerical_gradient, relative_error


def chart():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    records, sample = (X - mean) / std, (table[new, 2:][0] - mean) / std
    record = records[np.argmin(cdist(sample[None, :], records)[0])]
    gap = sample - record
    exact = gap / np.sqrt(np.sum(gap**2))
    found = np.asarray(
        numerical_gradient(lambda v: np.sqrt(np.sum((v - record) ** 2)), sample.copy()),
        dtype=float,
    )
    number = np.arange(1, len(sample) + 1)
    size = np.sqrt(np.sum(found**2))
    error = relative_error(found, exact)
    return {
        "x": {
            "min": 0,
            "max": 30,
            "step": 5,
            "label": "measurement, in the data's order",
        },
        "y": {"min": -0.5, "max": 0.5, "step": 0.25, "label": "slope of the distance"},
        "lines": [
            {"style": "dashed", "label": "No slope", "x": [0, 30], "y": [0, 0]},
            {
                "style": "main",
                "label": "Your numerical gradient",
                "x": number,
                "y": found,
            },
        ],
        "points": [
            {"x": int(n), "y": float(e)} for n, e in zip(number, exact, strict=True)
        ],
        "readouts": [
            {"label": "Length of your gradient", "value": f"{size:.4f}"},
            {
                "label": "Relative error against the exact gradient",
                "value": f"{error:.1e}",
            },
        ],
        "description": (
            "Each of the 30 elements of your numerical gradient of the distance from the "
            "first new sample to its nearest record, with the exact gradient as points. "
            f"Your gradient's length is {size:.4f}, and its relative error against the "
            f"exact one is {error:.1e}."
        ),
    }
