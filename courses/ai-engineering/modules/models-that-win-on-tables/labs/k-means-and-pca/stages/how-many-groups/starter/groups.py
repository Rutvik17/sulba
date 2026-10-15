def plus_plus(Z, k, rng):
    """k starting centres drawn from the rows of Z by k-means++, one to a row."""
    raise NotImplementedError


def best_of(Z, k, starts, rng):
    """k-means from this many k-means++ starts: the groups of the one with the least
    inertia."""
    raise NotImplementedError


def silhouette(Z, labels):
    """The mean silhouette of the rows of Z in these groups."""
    raise NotImplementedError
