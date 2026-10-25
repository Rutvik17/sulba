"""A task's working days as a triangular distribution of its three estimates."""

import math


def mean(low: float, likely: float, high: float) -> float:
    """The mean days of a task estimated at low, likely and high days."""
    return (low + likely + high) / 3


def quantile(low: float, likely: float, high: float, q: float) -> float:
    """The days within which the task is done with the chance q."""
    if high == low:
        return low
    if q <= (likely - low) / (high - low):
        return low + math.sqrt(q * (high - low) * (likely - low))
    return high - math.sqrt((1 - q) * (high - low) * (high - likely))
