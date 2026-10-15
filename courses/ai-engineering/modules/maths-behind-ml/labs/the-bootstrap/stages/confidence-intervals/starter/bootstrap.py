def percentile_interval(distribution, confidence):
    """The low and high ends of the interval between the distribution's quantiles that leave
    (1 - confidence) / 2 of it outside on each side."""
    raise NotImplementedError


def basic_interval(estimate, distribution, confidence):
    """The percentile interval reflected about the estimate: 2 * estimate minus its high
    end, and 2 * estimate minus its low end."""
    raise NotImplementedError
