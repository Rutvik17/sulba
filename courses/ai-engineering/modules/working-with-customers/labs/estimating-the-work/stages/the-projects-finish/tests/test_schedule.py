import random
import statistics

import pytest

from schedule import OFFICE, Task, finish, simulate


def by_hand(tasks, days):
    """The finish, by moving each task's end later until no task starts before its
    prerequisites end."""
    ends = {task.name: days[task.name] for task in tasks}
    changed = True
    while changed:
        changed = False
        for task in tasks:
            start = max((ends[name] for name in task.after), default=0)
            if start + days[task.name] > ends[task.name]:
                ends[task.name] = start + days[task.name]
                changed = True
    return max(ends.values(), default=0)


@pytest.mark.id("tst_m9re3u")
def test_finish():
    """Gives the day the pilot ends with every task at its likely days"""
    assert finish(OFFICE, {task.name: task.likely for task in OFFICE}) == 21
    assert finish(OFFICE, {task.name: task.high for task in OFFICE}) == by_hand(
        OFFICE, {task.name: task.high for task in OFFICE}
    )


@pytest.mark.id("tst_973ahy")
def test_edges():
    """Runs tasks that wait for nothing side by side, and gives day 0 for no tasks"""
    side = [Task("a", 1, 2, 3), Task("b", 1, 2, 3)]
    assert finish(side, {"a": 4, "b": 7}) == 7
    chain = [Task("a", 1, 2, 3), Task("b", 1, 2, 3, ("a",))]
    assert finish(chain, {"a": 4, "b": 7}) == 11
    assert finish([], {}) == 0


@pytest.mark.id("tst_tn8fox")
def test_random_finish():
    """Matches moving ends later by hand, on random projects"""
    rng = random.Random(302)
    for _ in range(300):
        tasks = []
        for place in range(rng.randint(1, 8)):
            after = tuple(
                rng.sample([task.name for task in tasks], rng.randint(0, len(tasks)))
            )
            tasks.append(Task(f"t{place}", 1, 2, 3, after))
        days = {task.name: rng.uniform(0, 10) for task in tasks}
        assert finish(tasks, days) == pytest.approx(by_hand(tasks, days))


@pytest.mark.id("tst_6oa8je")
def test_simulate():
    """Draws each run's tasks in order from one generator made from the seed"""
    rng = random.Random(7)
    expected = []
    for _ in range(50):
        days = {
            task.name: rng.triangular(task.low, task.high, task.likely)
            for task in OFFICE
        }
        expected.append(finish(OFFICE, days))
    assert simulate(OFFICE, 50, 7) == pytest.approx(expected)
    assert simulate(OFFICE, 50, 7) == simulate(OFFICE, 50, 7)
    one = simulate([Task("only", 2, 4, 9)], 20_000, 8)
    assert statistics.fmean(one) == pytest.approx(5, abs=0.05)
    assert min(one) >= 2 and max(one) <= 9
