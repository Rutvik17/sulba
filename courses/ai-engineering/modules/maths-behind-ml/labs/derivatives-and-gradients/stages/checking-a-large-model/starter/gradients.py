def directional_slope(f, x, v, h=1e-6):
    """f's slope at x along the vector v, by a central difference."""
    raise NotImplementedError


def gradient_agrees(f, gradient, x, rng):
    """Whether gradient(x) gives f's slope at x along random directions drawn from rng."""
    raise NotImplementedError
