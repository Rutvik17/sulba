"""What the simulated runs say the team can promise."""


def promised(finishes: list[float], chance: float) -> float:
    """The fewest days within which the share chance of the runs finish."""
    raise NotImplementedError


def chance_by(finishes: list[float], day: float) -> float:
    """The share of the runs that finish by the end of the day given."""
    raise NotImplementedError
