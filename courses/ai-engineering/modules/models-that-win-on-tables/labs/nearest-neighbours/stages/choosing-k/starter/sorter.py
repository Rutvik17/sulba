def sort_beans(train, varieties, batch, k):
    """Each bean of batch named by its k nearest training beans, scaled by the training beans'
    statistics."""
    raise NotImplementedError


def choose_k(train, varieties, validation, validation_varieties, ks):
    """The share of the validation beans each k of ks names right, and the k that names the
    most, the smallest of any tied."""
    raise NotImplementedError
