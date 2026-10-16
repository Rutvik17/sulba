```python
def normalize(vectors):
    vectors = np.asarray(vectors, dtype=float)
    return vectors / np.linalg.norm(vectors, axis=-1, keepdims=True)


def similarities(queries, products):
    return normalize(queries) @ normalize(products).T
```

Dividing a vector by its length leaves its direction as it was, and the cosine depends on directions alone. Normalized, the model's embeddings have length 1, but cut to their first {% $fig.dimensions %} numbers they are between {% $fig.shortest %} and {% $fig.longest %} long. A dot product of the vectors as the file holds them would favour the longer ones, and would change the most similar product for {% $fig.moved %} of the {% $fig.queries %} queries.

Between the queries and the products, the similarities run from {% $fig.lowest %} to {% $fig.highest %}. A cosine on its own says little: what search uses is the order it puts the products in for each query.
