"""The office's pilot: its tasks, when it finishes, and many runs of it drawn at random."""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """A task of the work: its name, its low, likely and high days, and the tasks it waits for."""

    name: str
    low: float
    likely: float
    high: float
    after: tuple[str, ...] = ()


# The pilot for the benefits office, each task after the tasks it waits for.
OFFICE = [
    Task("pages", 2, 3, 6),
    Task("sign-in", 3, 5, 12),
    Task("answers", 4, 6, 10, ("pages",)),
    Task("test set", 3, 4, 8, ("pages",)),
    Task("gates", 2, 3, 5, ("answers", "test set")),
    Task("chat page", 3, 4, 7, ("sign-in",)),
    Task("review", 2, 4, 10, ("sign-in", "answers")),
    Task("deploy", 2, 3, 8, ("gates", "chat page", "review")),
    Task("pilot", 5, 5, 7, ("deploy",)),
]


def finish(tasks: list[Task], days: dict[str, float]) -> float:
    """The day the last task ends, when each task takes the days given for it and starts once
    every task it waits for has ended."""
    ends: dict[str, float] = {}
    for task in tasks:
        start = max((ends[before] for before in task.after), default=0)
        ends[task.name] = start + days[task.name]
    return max(ends.values(), default=0)


def simulate(tasks: list[Task], runs: int, seed: int) -> list[float]:
    """The finish of each of runs runs, each task's days drawn from its triangular
    distribution."""
    rng = random.Random(seed)
    finishes = []
    for _ in range(runs):
        days = {
            task.name: rng.triangular(task.low, task.high, task.likely)
            for task in tasks
        }
        finishes.append(finish(tasks, days))
    return finishes
