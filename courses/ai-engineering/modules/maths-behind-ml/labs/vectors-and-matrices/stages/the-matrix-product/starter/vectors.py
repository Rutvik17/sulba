def pairwise_dots(A, B):
    """The dot product of each row of A with each row of B, as an array of shape
    (len(A), len(B))."""
    raise NotImplementedError


def fast_distances(A, B):
    """The Euclidean distance from each row of A to each row of B, worked out from the
    dot products: each squared distance is a row's squared length, plus the other row's,
    less twice their dot product, and one below 0 counts as 0."""
    raise NotImplementedError
