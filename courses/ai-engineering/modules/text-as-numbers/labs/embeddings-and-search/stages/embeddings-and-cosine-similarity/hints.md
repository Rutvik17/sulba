`np.linalg.norm(vectors, axis=-1, keepdims=True)` gives each vector's length, in a shape that divides every number in its row.

---

With the queries and the products normalized, `queries @ products.T` holds every dot product, a row for each query.
