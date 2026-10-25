"""The desk's share of the office's contacts: each kind's share weighted by the office's own mix
of contacts, with its interval."""

from dataclasses import dataclass

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
    raise NotImplementedError
