def direction(mu0, mu1):
    """The vector of length 1 that points from mu0 to mu1."""
    raise NotImplementedError


def scores(Z, mu0, mu1):
    """Each row of Z's signed distance from the midpoint of mu0 and mu1, along the
    direction from mu0 to mu1: positive on mu1's side of the midpoint."""
    raise NotImplementedError
