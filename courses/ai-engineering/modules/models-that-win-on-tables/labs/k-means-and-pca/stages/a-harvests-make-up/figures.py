import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

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
# The starts and seed of the groupings, and the checks' tolerance and beans named alone.
STARTS, SEED = 10, 0
TOLERANCE, ALONE = 0.03, 20


def figures():
    table = pd.read_csv("data/beans.csv")
    train, harvest = table[table["set"] == 0], table[table["set"] == 1]
    X = train[MEASUREMENTS].to_numpy(dtype=float)
    V = harvest[MEASUREMENTS].to_numpy(dtype=float)
    mean, sd = X.mean(axis=0), X.std(axis=0)
    Z, H = (X - mean) / sd, (V - mean) / sd
    varieties, truth = train["variety"].to_numpy(), harvest["variety"].to_numpy()
    kinds = sorted(set(varieties))
    found = {
        "harvest": f"{len(V):,}",
        "tolerance": f"{TOLERANCE:g}",
        "alone": str(ALONE),
        "varieties": str(len(kinds)),
    }
    k, missing = len(kinds), {}
    while True:
        model = KMeans(k, n_init=STARTS, random_state=SEED).fit(Z)
        names = [
            pd.Series(varieties[model.labels_ == group]).value_counts().index[0]
            for group in range(k)
        ]
        left_out = sorted(set(kinds) - set(names))
        if not left_out:
            break
        missing[k] = left_out
        k += 1
    # The explanation names the one variety that the groups leave out, as many as there are
    # varieties and one more.
    left = {tuple(out) for out in missing.values()}
    assert len(missing) == 2 and len(left) == 1 and len(next(iter(left))) == 1
    named = np.array(names)[model.predict(H)]
    found["fewest"] = str(k)
    found["missing"] = next(iter(left))[0]
    found["right"] = f"{np.mean(named == truth):.1%}"
    found["wrong"] = f"{np.mean(named != truth):.1%}"
    errors = []
    for i, kind in enumerate(kinds):
        share, estimate = np.mean(truth == kind), np.mean(named == kind)
        errors.append(abs(estimate - share))
        found[f"kind_{i}"] = kind
        found[f"share_{i}"] = f"{share:.1%}"
        found[f"estimate_{i}"] = f"{estimate:.1%}"
    found["worst"] = f"{max(errors):.1%}"
    # The checks hold the make-up to the tolerance the brief states.
    assert max(errors) <= TOLERANCE
    return found
