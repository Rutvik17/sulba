The full search compares each query with every product. The shop's catalogue will grow far past these {% $fig.products %} products, so the search will look only where a query's nearest products are likely to be. An inverted file index groups the products into lists with k-means, each list around its centroid. A query searches only the lists whose centroids are nearest to it, and compares itself with their products alone.

Write:

```
build_index(product_vectors, lists=LISTS) -> the centroids, and each product's list
search_index(index, product_vectors, query_vectors, k, probes=PROBES) -> each query's
    first k products, and how many products each query compared
```

Find the lists with scikit-learn's `KMeans` on the normalized product vectors, and import it from `sklearn.cluster` at the top of `search.py`. A query's nearest lists are those whose centroids are the shortest distance from its normalized embedding. Within them, rank the products as `nearest` does.

Then choose `LISTS` and `PROBES`, the lists each query searches, on the {% $fig.validation %} validation queries in `data/queries.csv`: searching more lists finds more of what the full search finds, and compares more products. Four hidden checks test the index on the {% $fig.test %} test queries before it ships.
