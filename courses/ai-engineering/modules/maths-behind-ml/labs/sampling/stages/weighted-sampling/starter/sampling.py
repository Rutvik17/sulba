def weighted_choice(weights, size, rng):
    """size row numbers drawn with replacement, row i with probability weights[i] over the
    weights' total, each from one uniform number from rng.random."""
    raise NotImplementedError


def balanced_weights(labels):
    """A weight for each record of 1 over the number of records with its label."""
    raise NotImplementedError


def reweighted_mean(values, batch, weights):
    """The mean of values over all the records, estimated from a batch drawn with
    probabilities in proportion to weights."""
    raise NotImplementedError
