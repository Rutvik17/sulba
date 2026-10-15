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
K, STARTS, SEED = 9, 10, 0


def commonest(labels, varieties, group):
    counts = pd.Series(varieties[labels == group]).value_counts()
    # A name the explanation reports is never a tie.
    assert len(counts) == 1 or counts.iloc[0] > counts.iloc[1]
    return counts.index[0]


def figures():
    table = pd.read_csv("data/beans.csv")
    train, harvest = table[table["set"] == 0], table[table["set"] == 1]
    X = train[MEASUREMENTS].to_numpy(dtype=float)
    V = harvest[MEASUREMENTS].to_numpy(dtype=float)
    mean, sd = X.mean(axis=0), X.std(axis=0)
    Z, H = (X - mean) / sd, (V - mean) / sd
    varieties, truth = train["variety"].to_numpy(), harvest["variety"].to_numpy()

    def right(names, groups):
        return np.mean(np.array(names)[groups] == truth)

    variances = np.linalg.eigvalsh(np.cov(Z, rowvar=False))
    found = {
        "least": f"{variances[:2].sum() / variances.sum():.5%}",
        "most": f"{variances[-2:].sum() / variances.sum():.1%}",
        "k": str(K),
        "harvest": f"{len(V):,}",
    }

    model = KMeans(K, n_init=STARTS, random_state=SEED).fit(Z)
    names = [commonest(model.labels_, varieties, group) for group in range(K)]
    found["right"] = f"{right(names, model.predict(H)):.1%}"

    raw = KMeans(K, n_init=STARTS, random_state=SEED).fit(X)
    raw_names = [commonest(raw.labels_, varieties, group) for group in range(K)]
    largest = max(set(varieties), key=lambda v: X[varieties == v, 0].mean())
    # The scaled harvest set against centres in pixels, as the report would have scored it.
    mixed = raw.predict(H)
    found["largest"] = largest
    found["largest_groups"] = str(raw_names.count(largest))
    found["single"] = raw_names[mixed[0]]
    found["single_right"] = f"{right(raw_names, mixed):.1%}"
    # The cost says the unscaled groups split the largest beans' variety into several, and
    # that every harvest bean fell into one group.
    assert raw_names.count(largest) > 1
    assert (mixed == mixed[0]).all()

    counted = []
    for group in range(K):
        here = varieties[model.labels_ == group]
        counted.append(max(set(here), key=list(varieties).count))
    wrong = sum(a != b for a, b in zip(counted, names, strict=True))
    overall = pd.Series(varieties).value_counts().index[0]
    found["misnamed"] = str(wrong)
    found["counted_right"] = f"{right(counted, model.predict(H)):.1%}"
    found["overall"] = overall
    found["overall_groups"] = str(counted.count(overall))

    afresh = KMeans(K, n_init=STARTS, random_state=SEED).fit_predict(H)
    found["afresh_right"] = f"{right(names, afresh):.1%}"
    return found
