"""The smallest drop in score a comparison of two releases can be counted on to find."""

import math
from statistics import NormalDist


def detectable(error: float, alpha: float, power: float) -> float:
    """The smallest drop a one-sided test at level alpha finds with the power given, for a
    change with this standard error."""
    normal = NormalDist()
    return (normal.inv_cdf(1 - alpha) + normal.inv_cdf(power)) * error


def questions_needed(
    error: float, questions: int, drop: float, alpha: float, power: float
) -> int:
    """The fewest questions on which the test finds the drop with the power given, when this
    many questions give this standard error and more of them spread as these do."""
    return math.ceil(questions * (detectable(error, alpha, power) / drop) ** 2)
