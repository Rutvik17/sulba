Walk the fused ranking in order, keeping a row only if no row kept before it has its text, and stop when you have kept enough.

---

`client.post("/rerank", json=body)` sends the request to the reranker the client reaches. `results` comes sorted by score, not in the order sent: `rows[result["index"]]` is the passage a result scores.

---

`httpx.HTTPError` is what `client.post` raises for a timeout or a dropped connection, and what `response.raise_for_status()` raises for an error. Catch it, and give the passages in the fused ranking's order.
