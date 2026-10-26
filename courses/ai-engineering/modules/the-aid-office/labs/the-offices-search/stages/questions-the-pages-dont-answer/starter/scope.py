def closeness(conn, vector):
    """The cosine similarity of vector to the passage nearest to it, over every passage."""
    raise NotImplementedError


def threshold(similarities, keep):
    """The highest closeness that at least keep of the similarities reach."""
    raise NotImplementedError


def rates(office, others, limit):
    """The share of the office's questions whose closeness reaches limit, and the share of the
    other questions whose closeness falls below it."""
    raise NotImplementedError
