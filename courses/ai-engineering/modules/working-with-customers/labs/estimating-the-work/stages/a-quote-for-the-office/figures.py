import datetime
import math
import random

RUNS = 10_000

# The office's quote, as quote.py gives it.
START = datetime.date(2026, 11, 2)
DAY_RATE = 140_000
DAYS_OFF = {
    datetime.date(2026, 11, 11),
    datetime.date(2026, 11, 26),
    datetime.date(2026, 11, 27),
    datetime.date(2026, 12, 24),
    datetime.date(2026, 12, 25),
}

# The office's pilot, as schedule.py gives it: each task's low, likely and high days, and the
# tasks it waits for, each after the tasks it waits for.
OFFICE = [
    ("pages", 2, 3, 6, ()),
    ("sign-in", 3, 5, 12, ()),
    ("answers", 4, 6, 10, ("pages",)),
    ("test set", 3, 4, 8, ("pages",)),
    ("gates", 2, 3, 5, ("answers", "test set")),
    ("chat page", 3, 4, 7, ("sign-in",)),
    ("review", 2, 4, 10, ("sign-in", "answers")),
    ("deploy", 2, 3, 8, ("gates", "chat page", "review")),
    ("pilot", 5, 5, 7, ("deploy",)),
]


def finish(days):
    """The day the last task ends, each task starting once the tasks it waits for have ended."""
    ends = {}
    for name, _, _, _, after in OFFICE:
        ends[name] = max((ends[before] for before in after), default=0) + days[name]
    return max(ends.values())


def simulate(runs, seed):
    """Each run's finish, every task drawn in turn from one generator, as simulate draws it."""
    rng = random.Random(seed)
    return [
        finish(
            {
                name: rng.triangular(low, high, likely)
                for name, low, likely, high, _ in OFFICE
            }
        )
        for _ in range(runs)
    ]


def chance_by(finishes, day):
    return sum(finish <= day for finish in finishes) / len(finishes)


def date(day):
    return f"{day.day} {day:%B %Y}"


def dollars(cents):
    return f"${cents // 100:,}.{cents % 100:02}"


def figures():
    runs = sorted(simulate(RUNS, 0))
    days = math.ceil(runs[math.ceil(0.8 * RUNS) - 1])
    done_by, counted = START - datetime.timedelta(days=1), 0
    while counted < days:
        done_by += datetime.timedelta(days=1)
        counted += done_by.weekday() < 5 and done_by not in DAYS_OFF
    price = days * DAY_RATE
    # Thirds, the cents left over going to the earlier milestones.
    signed, demo, running = (price // 3 + (place < price % 3) for place in range(3))
    likely = finish({name: likely for name, _, likely, _, _ in OFFICE})
    off = sorted(DAYS_OFF)
    return {
        "runs": f"{RUNS:,}",
        "start": date(START),
        "rate": dollars(DAY_RATE),
        "off": ", ".join(f"{day.day} {day:%B}" for day in off[:-1])
        + f" and {off[-1].day} {off[-1]:%B}",
        "days": f"{days}",
        "done_by": date(done_by),
        "price": dollars(price),
        "signed": dollars(signed),
        "demo": dollars(demo),
        "running": dollars(running),
        "met": f"{chance_by(runs, days):.0%}",
        "likely": f"{likely:g}",
        "likely_price": dollars(math.ceil(likely) * DAY_RATE),
        "over_likely": f"{1 - chance_by(runs, likely):.1%}",
    }
