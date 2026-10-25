"""What each of the assistant's problems would have changed in the office's estimate: the
assistant's estimate with each problem alone, and with all four."""

import math
import random

DEADLINE = 25
RUNS = 10_000

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


def assistant(order=False, one_seed=False, summed=False, rounded_down=False):
    """The fixed estimate of the office's pilot, drawn task by task as estimate.py draws it, with
    the problems named put back."""
    columns = {}
    rng = random.Random(0)
    for name, low, likely, high, _ in OFFICE:
        if one_seed:
            rng = random.Random(0)
        mode, top = (high, likely) if order else (likely, high)
        columns[name] = [rng.triangular(low, top, mode) for _ in range(RUNS)]
    finishes = []
    for run in range(RUNS):
        days = {name: column[run] for name, column in columns.items()}
        finishes.append(sum(days.values()) if summed else finish(days))
    finishes.sort()
    eighty = finishes[math.ceil(0.8 * RUNS) - 1]
    days = int(eighty) if rounded_down else math.ceil(eighty)
    return days, sum(f <= DEADLINE for f in finishes) / RUNS, eighty, finishes


def figures():
    days, chance, eighty, finishes = assistant()
    order = assistant(order=True)
    one_seed = assistant(one_seed=True)
    summed = assistant(summed=True)
    rounded = assistant(rounded_down=True)
    every = assistant(order=True, one_seed=True, summed=True, rounded_down=True)
    met = sum(f <= rounded[0] for f in finishes) / RUNS
    return {
        "deadline": f"{DEADLINE}",
        "days": f"{days}",
        "chance": f"{chance:.0%}",
        "eighty": f"{eighty:.2f}",
        "order_days": f"{order[0]}",
        "order_chance": f"{order[1]:.0%}",
        "seed_days": f"{one_seed[0]}",
        "seed_chance": f"{one_seed[1]:.0%}",
        "summed_days": f"{summed[0]}",
        "summed_chance": f"{summed[1]:.0%}",
        "rounded_days": f"{rounded[0]}",
        "rounded_met": f"{met:.1%}",
        "every_days": f"{every[0]}",
        "every_chance": f"{every[1]:.0%}",
    }
