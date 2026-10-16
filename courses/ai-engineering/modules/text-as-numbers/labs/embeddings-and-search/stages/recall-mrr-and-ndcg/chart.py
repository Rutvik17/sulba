import numpy as np

from search import (
    load_embeddings,
    load_gains,
    ndcg_at_k,
    nearest,
    recall_at_k,
    reciprocal_rank,
    similarities,
)

# How many of each embedding's numbers the search keeps, from the first.
KEPT = [16, 32, 64, 128, 256]


def chart(k=10):
    queries, query_vectors = load_embeddings("data/queries.csv")
    products, product_vectors = load_embeddings("data/products.csv")
    gains = load_gains(queries, products)
    exact = gains == 1
    scores = {"nDCG": [], "Recall": [], "MRR": []}
    for kept in KEPT:
        found = similarities(query_vectors[:, :kept], product_vectors[:, :kept])
        ranked = nearest(found, k)
        pairs = list(zip(ranked, gains, exact, strict=True))
        scores["nDCG"].append(np.mean([ndcg_at_k(r, g, k) for r, g, _ in pairs]))
        scores["Recall"].append(np.mean([recall_at_k(r, e, k) for r, _, e in pairs]))
        scores["MRR"].append(np.mean([reciprocal_rank(r, e, k) for r, _, e in pairs]))
    scores = {
        name: [round(float(value), 4) for value in values]
        for name, values in scores.items()
    }
    styles = {"MRR": "faint", "Recall": "base", "nDCG": "main"}
    return {
        "x": {"min": 0, "max": 256, "step": 64, "label": "numbers kept"},
        "y": {"min": 0, "max": 1, "step": 0.25, "label": f"score of the first {k}"},
        "lines": [
            {"style": style, "label": name, "x": KEPT, "y": scores[name]}
            for name, style in styles.items()
        ],
        "points": [{"x": KEPT[-1], "y": scores[name][-1]} for name in styles],
        "readouts": [
            {
                "label": f"{name} at {k}, all {KEPT[-1]} numbers",
                "value": f"{scores[name][-1]:.3f}",
            }
            for name in ["nDCG", "Recall", "MRR"]
        ],
        "description": (
            f"nDCG, recall and MRR of each query's first {k} products, on average over "
            f"{len(queries)} queries, as the search keeps from {KEPT[0]} to "
            f"{KEPT[-1]} of each embedding's numbers. nDCG goes from "
            f"{scores['nDCG'][0]:.3f} to {scores['nDCG'][-1]:.3f}, recall from "
            f"{scores['Recall'][0]:.3f} to {scores['Recall'][-1]:.3f}, and MRR from "
            f"{scores['MRR'][0]:.3f} to {scores['MRR'][-1]:.3f}."
        ),
    }
