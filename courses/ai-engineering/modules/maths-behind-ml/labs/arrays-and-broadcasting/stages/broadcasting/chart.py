import numpy as np

from similar import column_stats, distances, split, standardize


def shares(A, B):
    """Each column's share of the squared distances from the rows of A to the rows of B."""
    by_column = np.array(
        [np.sum(distances(A[:, [j]], B[:, [j]]) ** 2) for j in range(A.shape[1])]
    )
    return by_column / by_column.sum()


def chart():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    with open("data/breast-cancer.csv") as file:
        names = file.readline().strip().split(",")[2:]
    records, _, new, _ = split(table)
    mean, std = column_stats(records)
    raw = shares(new, records)
    standard = shares(standardize(new, mean, std), standardize(records, mean, std))
    number = np.arange(1, len(names) + 1)
    areas = raw[names.index("mean_area")] + raw[names.index("worst_area")]
    return {
        "x": {
            "min": 0,
            "max": len(names),
            "step": 5,
            "label": "measurement, in the data's order",
        },
        "y": {
            "min": 0,
            "max": 0.8,
            "step": 0.1,
            "label": "share of the squared distance",
        },
        "lines": [
            {"style": "faint", "label": "Raw measurements", "x": number, "y": raw},
            {"style": "main", "label": "Standardized", "x": number, "y": standard},
        ],
        "points": [],
        "readouts": [
            {"label": "Mean and worst area, raw", "value": f"{areas:.1%}"},
            {"label": "Largest share, standardized", "value": f"{standard.max():.1%}"},
            {"label": "Smallest share, standardized", "value": f"{standard.min():.1%}"},
        ],
        "description": (
            f"Each of the {len(names)} measurements' share of the squared distances from the "
            f"{len(new)} new samples to the {len(records)} records. On the raw "
            f"measurements, the mean and worst area make up {areas:.1%}; standardized, "
            f"each measurement makes up between {standard.min():.1%} and "
            f"{standard.max():.1%}."
        ),
    }
