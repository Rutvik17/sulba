import numpy as np
import pandas as pd

MEASUREMENTS = [
    "Area",
    "Perimeter",
    "MajorAxisLength",
    "MinorAxisLength",
    "AspectRatio",
    "Eccentricity",
    "ConvexArea",
    "EquivDiameter",
    "Extent",
    "Solidity",
    "Roundness",
    "Compactness",
    "ShapeFactor1",
    "ShapeFactor2",
    "ShapeFactor3",
    "ShapeFactor4",
]
# The share of the variance the explanation asks how many components keep, how many of each
# component's largest weights it names, and the measurements it compares the scores with.
KEPT, NAMED = 0.95, 3
FOLLOWED = ["MajorAxisLength", "MinorAxisLength", "AspectRatio"]


def components(Z):
    variances, vectors = np.linalg.eigh(np.cov(Z, rowvar=False))
    variances, directions = variances[::-1], vectors[:, ::-1].T
    rows = np.arange(len(directions))
    signs = np.sign(directions[rows, np.abs(directions).argmax(axis=1)])
    return variances, directions * signs[:, np.newaxis]


def figures():
    table = pd.read_csv("data/beans.csv")
    X = table[table["set"] == 0][MEASUREMENTS].to_numpy(dtype=float)
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    variances, directions = components(Z)
    shares = variances / variances.sum()
    count = int(np.searchsorted(np.cumsum(shares), KEPT)) + 1
    found = {
        "measurements": str(len(MEASUREMENTS)),
        "train": f"{len(X):,}",
        "first": f"{shares[0]:.1%}",
        "second": f"{shares[1]:.1%}",
        "both": f"{shares[:2].sum():.1%}",
        "kept": f"{KEPT:.0%}",
        "count": str(count),
        "count_share": f"{shares[:count].sum():.1%}",
    }
    for i in range(2):
        heaviest = np.argsort(-np.abs(directions[i]))[:NAMED]
        for rank, column in enumerate(heaviest):
            found[f"name_{i}_{rank}"] = MEASUREMENTS[column]
            found[f"weight_{i}_{rank}"] = f"{directions[i, column]:.3f}".replace(
                "-", "−"
            )
    # How the scores on the first two components follow a bean's length, width and
    # elongation, as the explanation describes them.
    scores = Z @ directions[:2].T
    columns = {name: X[:, MEASUREMENTS.index(name)] for name in FOLLOWED}
    follow = {
        (i, name): np.corrcoef(scores[:, i], columns[name])[0, 1]
        for i in range(2)
        for name in FOLLOWED
    }
    assert follow[0, "MajorAxisLength"] > 0.9
    assert follow[1, "MinorAxisLength"] > 0 > follow[1, "AspectRatio"]
    found["length"] = f"{follow[0, 'MajorAxisLength']:.3f}"
    found["width"] = f"{follow[1, 'MinorAxisLength']:.3f}"
    found["ratio"] = f"{follow[1, 'AspectRatio']:.3f}".replace("-", "−")
    raw, raw_directions = components(X)
    found["raw_first"] = f"{raw[0] / raw.sum():.3%}"
    found["raw_name"] = MEASUREMENTS[int(np.abs(raw_directions[0]).argmax())]
    found["raw_weight"] = f"{np.abs(raw_directions[0]).max():.3f}"
    return found
