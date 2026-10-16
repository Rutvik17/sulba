```python
LISTS, PROBES = 128, 20


def build_index(product_vectors, lists=LISTS):
    kmeans = KMeans(n_clusters=lists, n_init=1, random_state=0)
    kmeans.fit(normalize(product_vectors))
    return kmeans.cluster_centers_, kmeans.labels_


def search_index(index, product_vectors, query_vectors, k, probes=PROBES):
    centroids, lists = index
    products, queries = normalize(product_vectors), normalize(query_vectors)
    distances = ((queries[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    searched = np.argsort(distances, axis=1, kind="stable")[:, :probes]
    found, compared = [], []
    for query, chosen in zip(queries, searched, strict=True):
        candidates = np.flatnonzero(np.isin(lists, chosen))
        scores = products[candidates] @ query
        found.append(candidates[np.argsort(-scores, kind="stable")[:k]])
        compared.append(len(candidates))
    return found, np.array(compared)
```

k-means puts each product in the list of its nearest centroid, so the products in a list are near each other, and a query's nearest products are most likely in the lists nearest to it. Not always: a product near a query can sit at the edge of a list whose centroid is farther away, and searching more lists finds more of them. With {% $fig.lists %} lists, holding from {% $fig.smallest %} to {% $fig.largest %} products each:

| Lists searched | Found, validation | Compared, validation | Found, test | Compared, test |
| --- | --- | --- | --- | --- |
| {% $fig.tried_1 %} | {% $fig.validation_recall_1 %} | {% $fig.validation_compared_1 %} | {% $fig.test_recall_1 %} | {% $fig.test_compared_1 %} |
| {% $fig.tried_5 %} | {% $fig.validation_recall_5 %} | {% $fig.validation_compared_5 %} | {% $fig.test_recall_5 %} | {% $fig.test_compared_5 %} |
| {% $fig.tried_20 %} | {% $fig.validation_recall_20 %} | {% $fig.validation_compared_20 %} | {% $fig.test_recall_20 %} | {% $fig.test_compared_20 %} |
| {% $fig.tried_128 %} | {% $fig.validation_recall_128 %} | {% $fig.validation_compared_128 %} | {% $fig.test_recall_128 %} | {% $fig.test_compared_128 %} |

Found is the share of the full search's first {% $fig.k %} products the index finds, and compared the share of the products each query is compared with, on average. Searching {% $fig.probes %} of the {% $fig.lists %} lists finds {% $fig.test_recall_20 %} of the full search's first {% $fig.k %} for the test queries while comparing each with {% $fig.test_compared_20 %} of the products. The test queries find a little less than the validation queries the settings were chosen on, which is why the choice leaves room on both sides of the checks.
