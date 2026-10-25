"""What the desk is worth to the office each month, and how long the pilot takes to pay for
itself."""

from kinds import Share
from mix import OFFICE, Estimate

# The office's figures: an agent's minutes on each kind of contact, and what an agent's minute
# costs it. The desk's machine costs HOST dollars an hour, the team's support SUPPORT dollars a
# month, and the pilot PRICE dollars, as the quote gave it.
MINUTES = {"question": 7, "case": 6, "callback": 4, "new": 9, "vague": 3}
AGENT = 0.75
HOST = 0.50
SUPPORT = 4_000
PRICE = 40_600


def seconds(runs: list[dict[str, str]], variant: str) -> dict[str, float]:
    """Each kind's mean seconds a trial for the variant, from runs.csv's rows."""
    raise NotImplementedError


def monthly(
    shares: dict[str, Share],
    durations: dict[str, float],
    volumes: dict[str, int] = OFFICE,
    minutes: dict[str, float] = MINUTES,
    agent: float = AGENT,
    host: float = HOST,
    support: float = SUPPORT,
    confidence: float = 0.95,
) -> Estimate:
    """The dollars a month the desk saves the office, net of its machine and support, less and
    plus z standard errors."""
    raise NotImplementedError


def payback(price: float, net: Estimate) -> Estimate:
    """The months the pilot takes to pay for itself at the net a month given, its ends from the
    net's, and infinity where the net doesn't pay."""
    raise NotImplementedError
