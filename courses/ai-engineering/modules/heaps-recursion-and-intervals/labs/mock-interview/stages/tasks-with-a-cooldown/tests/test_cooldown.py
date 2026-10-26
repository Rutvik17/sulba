import random
from collections import Counter

import pytest

from cooldown import least_time

COMMONEST = 50_000
OTHERS = 50_000
COOLDOWN = 100


def unit_by_unit(tasks, cooldown):
    """The time, by running a unit at a time the free task with the most runs left."""
    left = Counter(tasks)
    free_at = dict.fromkeys(left, 0)
    now = done = 0
    while done < len(tasks):
        ready = [task for task in left if left[task] and free_at[task] <= now]
        if ready:
            task = max(ready, key=lambda each: left[each])
            left[task] -= 1
            free_at[task] = now + cooldown + 1
            done += 1
        now += 1
    return now


@pytest.mark.id("tst_3fy8xw")
def test_least_time():
    """Gives the fewest units that run every task"""
    assert least_time(["A", "A", "A", "B", "B", "B"], 2) == 8
    assert least_time(list("AAAAAABCDEFG"), 2) == 16


@pytest.mark.id("tst_7s3ifj")
def test_edges():
    """Handles no tasks, no cooldown, one task, and more tasks than the gaps need"""
    assert least_time([], 3) == 0
    assert least_time(["A", "A", "A", "B", "B", "B"], 0) == 6
    assert least_time(["A"], 5) == 1
    assert least_time(list("ABCDEABCDE"), 2) == 10


@pytest.mark.id("tst_ns9rn7")
def test_random():
    """Matches running a unit at a time, on random tasks"""
    rng = random.Random(601)
    for _ in range(300):
        tasks = [rng.choice("ABCD") for _ in range(rng.randint(0, 12))]
        cooldown = rng.randint(0, 4)
        assert least_time(tasks, cooldown) == unit_by_unit(tasks, cooldown)


@pytest.mark.id("tst_r5cnlf")
def test_long():
    """Gives the time for many tasks in time"""
    rng = random.Random(602)
    tasks = ["A"] * COMMONEST + [
        rng.choice("BCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(OTHERS)
    ]
    rng.shuffle(tasks)
    assert least_time(tasks, COOLDOWN) == (COMMONEST - 1) * (COOLDOWN + 1) + 1
    tasks = [
        rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(COMMONEST + OTHERS)
    ]
    assert least_time(tasks, 3) == len(tasks)
