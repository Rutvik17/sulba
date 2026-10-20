import httpx


def embed(client: httpx.Client, texts: list[str]) -> list[list[float]]:
    response = client.post("/embeddings", json={"model": "shop-embeddings", "input": texts})
    response.raise_for_status()
    data = sorted(response.json()["data"], key=lambda item: item["index"])
    return [item["embedding"] for item in data]


def rerank(
    client: httpx.Client, query: str, documents: list[str], top_n: int | None = None
) -> list[tuple[int, float]]:
    body: dict = {"model": "shop-reranker", "query": query, "documents": documents}
    if top_n is not None:
        body["top_n"] = top_n
    response = client.post("/rerank", json=body)
    response.raise_for_status()
    return [(result["index"], result["relevance_score"]) for result in response.json()["results"]]
