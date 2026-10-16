def recall_at_k(ranked, relevant, k):
    """The share of the relevant products that are among the first k ranked, or 0 if no
    product is relevant."""
    raise NotImplementedError


def reciprocal_rank(ranked, relevant, k):
    """1 over the rank of the first relevant product among the first k, or 0 if none
    is."""
    raise NotImplementedError


def ndcg_at_k(ranked, gains, k):
    """The DCG of the first k ranked, over the DCG of the best ranking there is, or 0 if
    no product has a gain."""
    raise NotImplementedError
