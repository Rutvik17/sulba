def closeness(conn, vector):
    """The cosine similarity of vector to its nearest passage, over every passage."""
    return conn.execute(
        "SELECT 1 - min(embedding <=> %s) FROM passages", (vector,)
    ).fetchone()[0]


def threshold(similarities, keep):
    """The highest closeness that at least keep of the similarities reach."""
    ordered = sorted(similarities, reverse=True)
    for count, similarity in enumerate(ordered, start=1):
        if count / len(ordered) >= keep:
            return similarity
    raise ValueError("keep is above 1.")


def rates(office, others, limit):
    """The share of the office's questions whose closeness reaches limit, and the
    share of the other questions whose closeness falls below it."""
    kept = sum(similarity >= limit for similarity in office) / len(office)
    declined = sum(similarity < limit for similarity in others) / len(others)
    return kept, declined
