import random

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


def figures():
    likely = finish({name: likely for name, _, likely, _, _ in OFFICE})
    runs = simulate(RUNS, 0)
    return {
        "likely": f"{likely:g}",
        "runs": f"{RUNS:,}",
        "mean": f"{sum(runs) / len(runs):.1f}",
    }
