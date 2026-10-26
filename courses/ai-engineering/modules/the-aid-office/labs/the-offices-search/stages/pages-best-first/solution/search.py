CANDIDATES = 40
K = 60
PAGES = 5

FIND = """
WITH query AS (
    SELECT replace(plainto_tsquery('english', %(question)s)::text, '&', '|')::tsquery
        AS query
), meaning AS (
    SELECT id, row_number() OVER (ORDER BY distance, id) AS rank
    FROM (
        SELECT id, embedding <=> %(vector)s AS distance FROM passages
        WHERE %(vector)s::vector IS NOT NULL
        ORDER BY embedding <=> %(vector)s LIMIT %(candidates)s
    ) nearest
), matching AS (
    SELECT id, row_number() OVER (ORDER BY score DESC, id) AS rank
    FROM (
        SELECT id, ts_rank(words, query) AS score FROM passages, query
        WHERE words @@ query ORDER BY score DESC, id LIMIT %(candidates)s
    ) best
), fused AS (
    SELECT id, sum(score) AS score
    FROM (
        SELECT id, %(weight)s / (%(k)s + rank) AS score FROM meaning
        UNION ALL
        SELECT id, (1 - %(weight)s) / (%(k)s + rank) FROM matching
    ) scores
    GROUP BY id
    HAVING sum(score) > 0
)
SELECT page, id FROM (
    SELECT DISTINCT ON (page) page, id, score FROM fused JOIN passages USING (id)
    ORDER BY page, score DESC, id
) pages
ORDER BY score DESC, id
LIMIT %(pages)s
"""


def search(conn, vector, question, weight, pages=PAGES):
    """The pages that best answer the question, best first, each with its best
    passage: the CANDIDATES passages nearest to vector and the CANDIDATES whose words
    best match the question, fused by their ranks, the first ranking weighed by weight
    and the second by 1 - weight. With no vector, by its words alone."""
    parameters = {
        "question": question,
        "vector": vector,
        "candidates": CANDIDATES,
        "weight": float(weight),
        "k": K,
        "pages": pages,
    }
    return [(page, id_) for page, id_ in conn.execute(FIND, parameters)]


def hit_rate(found, answers):
    """The share of the questions whose page is among the pages found for it."""
    return sum(page in pages for pages, page in zip(found, answers, strict=True)) / len(
        answers
    )


def reciprocal_rank(found, answers):
    """The mean over the questions of 1 over the rank of its page among the pages
    found for it, or 0 when it isn't there."""
    total = 0.0
    for pages, page in zip(found, answers, strict=True):
        if page in pages:
            total += 1 / (pages.index(page) + 1)
    return total / len(answers)
