"""A task's working days as a triangular distribution of its three estimates."""


def mean(low: float, likely: float, high: float) -> float:
    """The mean days of a task estimated at low, likely and high days."""
    raise NotImplementedError


def quantile(low: float, likely: float, high: float, q: float) -> float:
    """The days within which the task is done with the chance q."""
    raise NotImplementedError
