import numpy as np
import pandas as pd

# The numbers in each of the model's embeddings, from its model card.
MODEL_DIMENSIONS = 768


def vectors(path):
    table = pd.read_csv(path, keep_default_na=False)
    columns = [column for column in table.columns if column.startswith("e_")]
    return table, table[columns].to_numpy(dtype=float)


def figures():
    queries, query_vectors = vectors("data/queries.csv")
    products, product_vectors = vectors("data/products.csv")
    lengths = np.linalg.norm(np.vstack([query_vectors, product_vectors]), axis=1)
    unit = query_vectors / np.linalg.norm(query_vectors, axis=1, keepdims=True)
    unit_products = product_vectors / np.linalg.norm(
        product_vectors, axis=1, keepdims=True
    )
    cosine = unit @ unit_products.T
    dot = query_vectors @ product_vectors.T
    # How many queries' most similar product changes when the vectors keep their
    # lengths.
    moved = (cosine.argmax(axis=1) != dot.argmax(axis=1)).sum()
    return {
        "queries": str(len(queries)),
        "products": f"{len(products):,}",
        "dimensions": str(query_vectors.shape[1]),
        "model_dimensions": str(MODEL_DIMENSIONS),
        "shortest": f"{lengths.min():.2f}",
        "longest": f"{lengths.max():.2f}",
        "lowest": f"{cosine.min():.2f}".replace("-", "−"),
        "highest": f"{cosine.max():.2f}",
        "moved": str(moved),
    }
