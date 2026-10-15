def network_loss(params, Z, y):
    """The mean log loss of a network with one hidden layer of tanh units. params is
    (W1, b1, w2, b2), each row of Z is a sample, and y holds the diagnoses, 0 or 1."""
    raise NotImplementedError


def network_gradient(params, Z, y):
    """The derivatives of network_loss with respect to W1, b1, w2 and b2, by the chain
    rule: a tuple in that order, each of its parameter's shape."""
    raise NotImplementedError
