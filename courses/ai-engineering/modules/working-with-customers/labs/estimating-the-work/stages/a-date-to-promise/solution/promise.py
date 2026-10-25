"""What the simulated runs say the team can promise."""

import math


def promised(finishes: list[float], chance: float) -> float:
    """The fewest days within which the share chance of the runs finish."""
    ordered = sorted(finishes)
    return ordered[max(math.ceil(chance * len(ordered)) - 1, 0)]


def chance_by(finishes: list[float], day: float) -> float:
    """The share of the runs that finish by the end of the day given."""
    return sum(finish <= day for finish in finishes) / len(finishes)
