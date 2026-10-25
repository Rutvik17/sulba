"""The office's estimate: the days the team can promise, and the chance of the office's date."""

import math
import random

import schedule


def estimate(
    tasks: list[schedule.Task], deadline: float, runs: int = 10_000, seed: int = 0
) -> tuple[int, float]:
    """The whole days within which four runs in five finish, and the share of runs that finish by
    the end of the deadline's day."""
    # Each task's days in every run, drawn task by task.
    columns = {}
    rng = random.Random(seed)
    for task in tasks:
        columns[task.name] = [
            rng.triangular(task.low, task.high, task.likely) for _ in range(runs)
        ]
    finishes = []
    for run in range(runs):
        days = {name: column[run] for name, column in columns.items()}
        finishes.append(schedule.finish(tasks, days))
    finishes.sort()
    eighty = finishes[math.ceil(0.8 * runs) - 1]
    chance = sum(finish <= deadline for finish in finishes) / runs
    return math.ceil(eighty), chance
