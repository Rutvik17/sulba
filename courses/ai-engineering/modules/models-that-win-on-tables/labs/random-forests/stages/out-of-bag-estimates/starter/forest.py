def out_of_bag(trees, samples, X):
    """Each row's share of yes averaged over the trees whose sample left it out, or NaN where
    every sample held it."""
    raise NotImplementedError
