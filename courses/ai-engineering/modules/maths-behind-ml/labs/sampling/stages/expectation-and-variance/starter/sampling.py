def batch_mean_variance(values, size):
    """The variance of the mean of values over a random batch of size rows, drawn without
    replacement."""
    raise NotImplementedError


def simulated_means(values, size, rng, repeats):
    """The means of values over repeats random batches of size rows, each drawn without
    replacement with rng."""
    raise NotImplementedError
