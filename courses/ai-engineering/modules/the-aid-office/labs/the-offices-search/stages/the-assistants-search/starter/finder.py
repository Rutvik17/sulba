import httpx
import numpy as np

EMBEDDER = "nomic-embed-text-v1.5"
QUERY = "search_query: "
CLOSE = 0.7
WEIGHT = 0.8
TIMEOUT = 5

PAGES = """
WITH query AS (
    SELECT plainto_tsquery('english', %(question)s) AS query
), meaning AS (
    SELECT id, row_number() OVER (ORDER BY distance, id) AS rank
    FROM (
        SELECT id, embedding <=> %(vector)s AS distance FROM passages
        WHERE %(vector)s::vector IS NOT NULL
        ORDER BY embedding <=> %(vector)s LIMIT 40
    ) nearest
), matching AS (
    SELECT id, row_number() OVER (ORDER BY score DESC, id) AS rank
    FROM (
        SELECT id, ts_rank(words, query) AS score FROM passages, query
        WHERE words @@ query ORDER BY score DESC, id LIMIT 40
    ) best
), fused AS (
    SELECT id, sum(score) AS score
    FROM (
        SELECT id, %(weight)s / (60 + rank) AS score FROM meaning
        UNION ALL
        SELECT id, (1 - %(weight)s) / (60 + rank) FROM matching
    ) scores
    GROUP BY id
    HAVING sum(score) > 0
)
SELECT DISTINCT ON (page) page, id FROM fused JOIN passages USING (id)
ORDER BY page, score DESC, id
LIMIT 5
"""


def embedding(client, question):
    """The question's vector from the model, as a query."""
    response = client.post(
        "/embeddings",
        json={"model": EMBEDDER, "input": [QUERY + question]},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return np.array(response.json()["data"][0]["embedding"], dtype=np.float32)


def answerable(conn, vector):
    """Whether a passage is close enough to the question's vector to answer it."""
    [closest] = conn.execute(
        "SELECT min(embedding <=> %s) FROM passages", (vector,)
    ).fetchone()
    return closest >= CLOSE


def pages(conn, vector, question):
    """The five pages that best answer the question, best first, each with its
    best passage."""
    weight = WEIGHT if vector is not None else 0.0
    parameters = {"question": question, "vector": vector, "weight": weight}
    return [(page, id_) for page, id_ in conn.execute(PAGES, parameters)]


def find(conn, client, question):
    """The pages for the question: none when no passage is close enough, and by its
    words alone when the model can't embed it."""
    try:
        vector = embedding(client, question)
    except httpx.HTTPStatusError:
        return pages(conn, None, question)
    if not answerable(conn, vector):
        return []
    return pages(conn, vector, question)
