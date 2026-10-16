The shop's search shows a list of products for whatever a shopper types. It will rank them with an embedding model that runs on its own machine, Snowflake's arctic-embed-m-v1.5. The model turns a text into a vector of {% $fig.model_dimensions %} numbers, its embedding, so that texts that mean much the same get vectors that point the same way. Its model card puts a prefix before each query, and none before a document, here a product's title.

`data/queries.csv` holds {% $fig.queries %} shoppers' queries from Amazon's Shopping Queries Dataset, and `data/products.csv` the {% $fig.products %} products people judged for them. Each comes with the first {% $fig.dimensions %} numbers of its embedding, in `e_1` onwards: the model was trained so that its first numbers make a good embedding on their own, and its model card keeps the first {% $fig.dimensions %} to search with.

How alike two vectors are is the cosine of the angle between them:

```math
\cos(q, p) = \frac{q \cdot p}{\|q\| \, \|p\|}
```

Start `search.py`, where `load_embeddings` in the starter reads a file of embeddings. Write:

```
normalize(vectors) -> each vector divided by its length
similarities(queries, products) -> the cosine similarity of each query with each product
```

Once two vectors are normalized, their cosine is their dot product, so one matrix product gives every query's similarity with every product. The tests compare yours with scikit-learn's.
