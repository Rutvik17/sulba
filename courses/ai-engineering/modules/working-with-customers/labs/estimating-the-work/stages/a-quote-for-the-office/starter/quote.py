"""The quote the office reads: the days promised, the day the pilot is done, and its price."""

import datetime
from dataclasses import dataclass

# The office's quote: work starts on a Monday, the team's day rate in cents, the days the
# team doesn't work besides weekends, and each milestone's share of the price.
START = datetime.date(2026, 11, 2)
DAY_RATE = 140_000
DAYS_OFF = frozenset(
    {
        datetime.date(2026, 11, 11),
        datetime.date(2026, 11, 26),
        datetime.date(2026, 11, 27),
        datetime.date(2026, 12, 24),
        datetime.date(2026, 12, 25),
    }
)
MILESTONES = {"signed": 1, "demo": 1, "pilot running": 1}


@dataclass(frozen=True)
class Quote:
    """The whole working days promised, the last of them, the price in cents, and each
    milestone's payment in cents."""

    days: int
    done_by: datetime.date
    price: int
    payments: dict[str, int]


def quote(
    finishes: list[float],
    start: datetime.date = START,
    day_rate: int = DAY_RATE,
    milestones: dict[str, int] = MILESTONES,
    days_off: frozenset[datetime.date] = DAYS_OFF,
) -> Quote:
    """The quote for a project whose simulated finishes are given."""
    raise NotImplementedError
