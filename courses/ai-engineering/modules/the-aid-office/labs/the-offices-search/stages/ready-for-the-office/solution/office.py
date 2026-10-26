import httpx
import numpy as np

from scope import closeness
from search import search

EMBEDDER = "nomic-embed-text-v1.5"
QUERY = "search_query: "
# The closeness that 95% of the office's validation questions reach, the weight of
# meaning in the fused search, and the seconds the model has to embed a question.
LIMIT = 0.7085
WEIGHT = 0.8
TIMEOUT = 5


def embedding(client, question):
    response = client.post(
        "/embeddings",
        json={"model": EMBEDDER, "input": [QUERY + question]},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return np.array(response.json()["data"][0]["embedding"], dtype=np.float32)


def find(conn, client, question):
    """The office's pages that best answer the question, best first, each with its
    best passage: none when no passage is close enough, and by its words alone when
    the model can't embed it."""
    try:
        vector = embedding(client, question)
    except httpx.HTTPError, KeyError, IndexError, ValueError:
        return search(conn, None, question, 0)
    if closeness(conn, vector) < LIMIT:
        return []
    return search(conn, vector, question, WEIGHT)
