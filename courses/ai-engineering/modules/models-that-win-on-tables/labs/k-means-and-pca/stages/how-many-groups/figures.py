import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

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
# The explanation's groups and seeds for comparing starts, the starts it takes the best of,
# and the chart's numbers of groups, starts and seed.
K, SEEDS, BEST_OF = 7, 10, 10
KS, STARTS, SEED = range(2, 11), 10, 0


def assign(Z, centres):
    distances = ((Z[:, np.newaxis, :] - centres[np.newaxis, :, :]) ** 2).sum(axis=2)
    return distances.argmin(axis=1)


def k_means(Z, centres):
    labels = assign(Z, centres)
    groups = range(len(centres))
    while True:
        centres = np.array([Z[labels == group].mean(axis=0) for group in groups])
        moved = assign(Z, centres)
        if np.array_equal(moved, labels):
            break
        labels = moved
    return labels, centres, float(((Z - centres[labels]) ** 2).sum())


def plus_plus(Z, k, rng):
    centres = [Z[rng.integers(len(Z))]]
    nearest = ((Z - centres[0]) ** 2).sum(axis=1)
    while len(centres) < k:
        centres.append(Z[rng.choice(len(Z), p=nearest / nearest.sum())])
        nearest = np.minimum(nearest, ((Z - centres[-1]) ** 2).sum(axis=1))
    return np.array(centres)


def spread(inertias):
    return [
        f"{value:,.1f}" for value in (min(inertias), np.mean(inertias), max(inertias))
    ]


def figures():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0]
    X = train[MEASUREMENTS].to_numpy(dtype=float)
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    varieties = train["variety"].to_numpy()
    found = {"k": str(K), "seeds": str(SEEDS), "best_of": str(BEST_OF)}
    rows, plus, best = [], [], []
    for seed in range(SEEDS):
        rng = np.random.default_rng(seed)
        rows.append(k_means(Z, Z[rng.choice(len(Z), K, replace=False)])[2])
        plus.append(k_means(Z, plus_plus(Z, K, np.random.default_rng(seed)))[2])
        rng = np.random.default_rng(seed)
        best.append(min(k_means(Z, plus_plus(Z, K, rng))[2] for _ in range(BEST_OF)))
    for name, inertias in [("rows", rows), ("plus", plus), ("best", best)]:
        low, mean, high = spread(inertias)
        found[f"{name}_low"], found[f"{name}_mean"], found[f"{name}_high"] = (
            low,
            mean,
            high,
        )
    # The explanation says one start of either kind differs by hundreds from seed to seed,
    # and the best of several by less than 1.
    assert min(np.ptp(rows), np.ptp(plus)) > 100 and np.ptp(best) < 1

    scores, shares = {}, {}
    for k in KS:
        labels = KMeans(k, n_init=STARTS, random_state=SEED).fit(Z).labels_
        scores[k] = silhouette_score(Z, labels)
        commonest = sum(
            pd.Series(varieties[labels == group]).value_counts().iloc[0]
            for group in range(k)
        )
        shares[k] = commonest / len(Z)
    top = max(scores, key=scores.get)
    varieties_count = len(set(varieties))
    # The explanation compares the best-separated grouping with one group for each variety.
    assert top < varieties_count
    found.update(
        {
            "low_k": str(KS[0]),
            "high_k": str(KS[-1]),
            "starts": str(STARTS),
            "top": str(top),
            "top_score": f"{scores[top]:.3f}",
            "top_share": f"{shares[top]:.1%}",
            "varieties": str(varieties_count),
            "varieties_score": f"{scores[varieties_count]:.3f}",
            "varieties_share": f"{shares[varieties_count]:.1%}",
            "high_share": f"{shares[KS[-1]]:.1%}",
        }
    )
    return found
