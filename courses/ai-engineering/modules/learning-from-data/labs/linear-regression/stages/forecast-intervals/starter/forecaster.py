def halfwidth(misses, coverage=0.9):
    """How far either side of a forecast its interval reaches, from the misses on n
    hours the model didn't fit: the ceil((n + 1) * coverage)-th smallest miss size, or
    inf when that is more than n."""
    raise NotImplementedError


def intervals(forecaster, weather, q):
    """The low and high ends of each hour's interval, as (low, high)."""
    raise NotImplementedError
