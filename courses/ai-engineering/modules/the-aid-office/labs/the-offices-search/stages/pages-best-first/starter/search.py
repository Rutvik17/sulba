CANDIDATES = 40
K = 60
PAGES = 5


def search(conn, vector, question, weight, pages=PAGES):
    """The pages that best answer the question, best first, each with its best passage."""
    raise NotImplementedError


def hit_rate(found, answers):
    """The share of the questions whose page is among the pages found for it."""
    raise NotImplementedError


def reciprocal_rank(found, answers):
    """The mean over the questions of 1 over the rank of its page among the pages found for it,
    or 0 when it isn't there."""
    raise NotImplementedError
