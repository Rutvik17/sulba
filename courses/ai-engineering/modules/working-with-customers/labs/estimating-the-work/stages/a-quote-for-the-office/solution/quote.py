"""The quote the office reads: the days promised, the day the pilot is done, and its price."""

import datetime
import math
from dataclasses import dataclass

from promise import promised

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


def working_day(
    start: datetime.date, days: int, days_off: frozenset[datetime.date]
) -> datetime.date:
    """The last of the days working days counted from start, start among them if it's one."""
    day = start - datetime.timedelta(days=1)
    while days > 0:
        day += datetime.timedelta(days=1)
        if day.weekday() < 5 and day not in days_off:
            days -= 1
    return day


def payments(price: int, milestones: dict[str, int]) -> dict[str, int]:
    """The price split by the milestones' shares, in whole cents adding up to the price."""
    total = sum(milestones.values())
    paid = {name: price * share // total for name, share in milestones.items()}
    left = price - sum(paid.values())
    remainders = sorted(
        milestones, key=lambda name: price * milestones[name] % total, reverse=True
    )
    for name in remainders[:left]:
        paid[name] += 1
    return paid


def quote(
    finishes: list[float],
    start: datetime.date = START,
    day_rate: int = DAY_RATE,
    milestones: dict[str, int] = MILESTONES,
    days_off: frozenset[datetime.date] = DAYS_OFF,
) -> Quote:
    """The quote for a project whose simulated finishes are given."""
    if not finishes:
        raise ValueError("no finishes to promise from")
    if day_rate <= 0:
        raise ValueError("the day rate must be above 0")
    if not milestones or min(milestones.values()) <= 0:
        raise ValueError("every milestone needs a share above 0")
    days = math.ceil(promised(finishes, 0.8))
    price = days * day_rate
    return Quote(
        days, working_day(start, days, days_off), price, payments(price, milestones)
    )
