import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

# How many products the search shows, the shares the checks hold the index to, the lists
# and probes the solution uses, and the probes the explanation compares at those lists.
K, RECALL, COMPARED = 10, 0.95, 0.30
LISTS, PROBES = 128, 20
TRIED = [1, 5, 20, 128]


def vectors(path):
    table = pd.read_csv(path, keep_default_na=False)
    columns = [column for column in table.columns if column.startswith("e_")]
    vectors = table[columns].to_numpy(dtype=float)
    return table, vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def figures():
    queries, query_vectors = vectors("data/queries.csv")
    products, product_vectors = vectors("data/products.csv")
    kmeans = KMeans(n_clusters=LISTS, n_init=1, random_state=0).fit(product_vectors)
    centroids, lists = kmeans.cluster_centers_, kmeans.labels_
    sizes = np.bincount(lists, minlength=LISTS)
    full = np.argsort(-(query_vectors @ product_vectors.T), axis=1, kind="stable")[
        :, :K
    ]
    distances = ((query_vectors[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    order = np.argsort(distances, axis=1, kind="stable")
    values = {
        "k": str(K),
        "products": f"{len(products):,}",
        "recall_target": f"{RECALL:.0%}",
        "compared_target": f"{COMPARED:.0%}",
        "lists": str(LISTS),
        "probes": str(PROBES),
        "smallest": str(sizes.min()),
        "largest": str(sizes.max()),
    }
    for part in ["validation", "test"]:
        rows = np.flatnonzero(queries["set"] == part)
        values[part] = str(len(rows))
        for probes in TRIED:
            found, compared = [], []
            for row in rows:
                candidates = np.flatnonzero(np.isin(lists, order[row, :probes]))
                scores = product_vectors[candidates] @ query_vectors[row]
                top = candidates[np.argsort(-scores, kind="stable")[:K]]
                found.append(np.isin(top, full[row]).mean())
                compared.append(len(candidates) / len(products))
            values[f"{part}_recall_{probes}"] = f"{np.mean(found):.1%}"
            values[f"{part}_compared_{probes}"] = f"{np.mean(compared):.1%}"
    for probes in TRIED:
        values[f"tried_{probes}"] = str(probes)
    return values
