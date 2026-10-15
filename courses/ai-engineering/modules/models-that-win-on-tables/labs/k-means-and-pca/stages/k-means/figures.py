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
# The explanation's groups, and the seed that draws the training beans they start from.
K, SEED = 7, 0


def assign(Z, centres):
    distances = ((Z[:, np.newaxis, :] - centres[np.newaxis, :, :]) ** 2).sum(axis=2)
    return distances.argmin(axis=1)


def figures():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0]
    X = train[MEASUREMENTS].to_numpy(dtype=float)
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    rng = np.random.default_rng(SEED)
    centres = Z[rng.choice(len(Z), K, replace=False)]
    labels, inertias = assign(Z, centres), []
    while True:
        centres = np.array([Z[labels == group].mean(axis=0) for group in range(K)])
        inertias.append(((Z - centres[labels]) ** 2).sum())
        moved = assign(Z, centres)
        if np.array_equal(moved, labels):
            break
        labels = moved
    # The explanation says the inertia fell in every round.
    assert (np.diff(inertias) < 0).all()
    found = {
        "k": str(K),
        "rounds": str(len(inertias) + 1),
        "inertia": f"{inertias[-1]:,.1f}",
    }
    varieties = train["variety"].to_numpy()
    groups = []
    for group in range(K):
        counts = pd.Series(varieties[labels == group]).value_counts()
        groups.append(
            (int(counts.sum()), counts.index[0], counts.iloc[0] / counts.sum())
        )
    groups.sort(key=lambda each: -each[0])
    for i, (beans, variety, share) in enumerate(groups):
        found[f"beans_{i}"] = f"{beans:,}"
        found[f"variety_{i}"] = variety
        found[f"share_{i}"] = f"{share:.1%}"
    commonest = pd.Series([variety for _, variety, _ in groups]).value_counts()
    # The explanation names the one variety that is the commonest of two groups, and the one
    # that is the commonest of none.
    assert commonest.iloc[0] == 2 and commonest.iloc[1] == 1
    missing = sorted(set(varieties) - set(commonest.index))
    assert len(missing) == 1
    found["twice"] = commonest.index[0]
    found["missing"] = missing[0]
    found["varieties"] = str(len(set(varieties)))
    return found
