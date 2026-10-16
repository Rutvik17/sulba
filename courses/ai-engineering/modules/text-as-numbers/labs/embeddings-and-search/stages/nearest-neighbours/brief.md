For each query, the search shows the products whose embeddings are the most similar to the query's: its nearest neighbours. Write:

```
nearest(similarities, k) -> for each query, the indexes of its k most similar products
```

The most similar product comes first. Of products whose similarities tie, the one that comes first in `data/products.csv` goes first: {% $fig.same %} products have exactly the same embedding as another product, so ties happen.

The tests compare yours with scikit-learn's `NearestNeighbors`, which ranks by cosine distance, 1 minus the cosine similarity.
