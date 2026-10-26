"""The desk's share of the office's contacts: each kind's share weighted by the office's own mix
of contacts, with its interval."""

import math
from dataclasses import dataclass
from statistics import NormalDist

from kinds import Share

# The office's chat contacts a month, by kind.
OFFICE = {"question": 3_000, "case": 900, "callback": 700, "new": 400, "vague": 200}


@dataclass(frozen=True)
class Estimate:
    """An estimate with its interval."""

    value: float
    low: float
    high: float


def weighted(
    shares: dict[str, Share], volumes: dict[str, int], confidence: float = 0.95
) -> Estimate:
    """The share of the contacts the desk does, each kind weighted by its share of the
    contacts, less and plus z standard errors, z for the confidence, within 0 and 1."""
    total = sum(volumes.values())
    if total <= 0 or any(kind not in shares for kind in volumes):
        raise ValueError("every kind needs a share, and there must be contacts")
    weights = {kind: count / total for kind, count in volumes.items()}
    value = sum(weight * shares[kind].value for kind, weight in weights.items())
    error = math.sqrt(
        sum((weight * shares[kind].error) ** 2 for kind, weight in weights.items())
    )
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    return Estimate(value, max(value - z * error, 0.0), min(value + z * error, 1.0))
