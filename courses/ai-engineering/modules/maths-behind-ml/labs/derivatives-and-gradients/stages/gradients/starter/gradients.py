def numerical_gradient(f, x, h=1e-6):
    """The gradient of f at the vector x: a central difference for each element in turn,
    leaving x as it was."""
    raise NotImplementedError


def relative_error(a, b):
    """The length of a - b as a share of the longer of a and b, or 0 when both are 0."""
    raise NotImplementedError
