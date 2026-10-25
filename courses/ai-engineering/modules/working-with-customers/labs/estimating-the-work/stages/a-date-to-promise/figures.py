import math
import random
import statistics

RUNS = 10_000
DEADLINE = 25

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


def promised(finishes, chance):
    ordered = sorted(finishes)
    return ordered[max(math.ceil(chance * len(ordered)) - 1, 0)]


def chance_by(finishes, day):
    return sum(finish <= day for finish in finishes) / len(finishes)


def eighty(low, likely, high):
    """The task's days within which it's done with a chance of 80%."""
    if 0.8 <= (likely - low) / (high - low):
        return low + math.sqrt(0.8 * (high - low) * (likely - low))
    return high - math.sqrt(0.2 * (high - low) * (high - likely))


def figures():
    runs = simulate(RUNS, 0)
    likely = finish({name: likely for name, _, likely, _, _ in OFFICE})
    chained = finish(
        {name: eighty(low, likely, high) for name, low, likely, high, _ in OFFICE}
    )
    p80 = promised(runs, 0.8)
    # The explanation says statistics.quantiles agrees to within a few hundredths of a day.
    assert abs(statistics.quantiles(runs, n=5)[3] - p80) < 0.05
    return {
        "deadline": f"{DEADLINE}",
        "likely": f"{likely:g}",
        "runs": f"{RUNS:,}",
        "p50": f"{promised(runs, 0.5):.1f}",
        "p80": f"{p80:.1f}",
        "p95": f"{promised(runs, 0.95):.1f}",
        "on_likely": f"{chance_by(runs, likely):.1%}",
        "on_deadline": f"{chance_by(runs, DEADLINE):.0%}",
        "chained": f"{chained:.1f}",
    }
