import numpy as np
import pandas as pd

# How many products the search shows for each query.
K = 10


def vectors(path):
    table = pd.read_csv(path, keep_default_na=False)
    columns = [column for column in table.columns if column.startswith("e_")]
    vectors = table[columns].to_numpy(dtype=float)
    return table, vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def figures():
    queries, query_vectors = vectors("data/queries.csv")
    products, product_vectors = vectors("data/products.csv")
    judgements = pd.read_csv("data/judgements.csv", keep_default_na=False)
    ranked = np.argsort(-(query_vectors @ product_vectors.T), axis=1, kind="stable")[
        :, :K
    ]
    shown = pd.DataFrame(
        {
            "query_id": np.repeat(queries["query_id"].to_numpy(), K),
            "product_id": products["product_id"].to_numpy()[ranked.ravel()],
        }
    )
    found = shown.merge(judgements, on=["query_id", "product_id"], how="left")
    judged = found["label"].notna().groupby(found["query_id"]).sum()
    exact = (found["label"] == "E").groupby(found["query_id"]).sum()
    same = pd.DataFrame(product_vectors).duplicated(keep=False).sum()
    return {
        "k": str(K),
        "judged": f"{judged.mean():.1f}",
        "exact": f"{exact.mean():.1f}",
        "none_exact": str((exact == 0).sum()),
        "queries": str(len(queries)),
        "same": str(same),
    }
