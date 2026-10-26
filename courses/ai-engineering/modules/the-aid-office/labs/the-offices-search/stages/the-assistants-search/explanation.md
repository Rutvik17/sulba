`plainto_tsquery` puts `&` between the words it keeps, as Postgres's documentation says. A student's question is a sentence, and few passages hold every word of one. With `|`, any of its words match, and `ts_rank` puts the passages that hold more of them first.

Postgres's documentation says the `DISTINCT ON` expressions must match the leftmost `ORDER BY` expressions, so a query that keeps each page's best passage gives its rows in page order, and only an outer query can sort them by score.

pgvector's `<=>` gives the cosine distance, 1 less the cosine similarity, so the nearest passage has the least. A closeness needs the similarity, 1 less that distance.

httpx's errors share one base class, `httpx.HTTPError`: a reply with an error status raises `httpx.HTTPStatusError` from `raise_for_status`, and a request that fails before a reply, by a dropped connection or a timeout, raises an `httpx.RequestError`. Searching by words whenever the model can't give a vector takes catching both.
