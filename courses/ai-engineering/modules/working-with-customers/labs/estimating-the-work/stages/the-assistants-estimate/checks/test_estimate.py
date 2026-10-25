import pytest

from estimate import estimate
from schedule import Task


@pytest.mark.id("tst_26v22z")
def test_a_task_drawn_from_its_estimates():
    """A task of 0, 1 and 10 days is done by day 5 in about 72% of runs"""
    # F(5) = 1 - (10 - 5)^2 / ((10 - 0) * (10 - 1)) = 0.7222...
    for seed in range(3):
        _, chance = estimate([Task("only", 0, 1, 10)], 5, seed=seed)
        assert chance == pytest.approx(1 - 25 / 90, abs=0.02)


@pytest.mark.id("tst_znmcfp")
def test_tasks_drawn_apart():
    """Two tasks in a row of 0, 10 and 10 days each are done by day 10 in about 1 run in 6"""
    # The chance that two draws with density x / 50 on [0, 10] add to at most 10 is 1/6.
    tasks = [Task("first", 0, 10, 10), Task("second", 0, 10, 10, ("first",))]
    for seed in range(3):
        _, chance = estimate(tasks, 10, seed=seed)
        assert chance == pytest.approx(1 / 6, abs=0.02)


@pytest.mark.id("tst_a88syc")
def test_tasks_side_by_side():
    """Tasks that wait for nothing run at once"""
    tasks = [Task("pages", 5, 5, 5), Task("sign-in", 3, 3, 3)]
    assert estimate(tasks, 10)[0] == 5


@pytest.mark.id("tst_v87shp")
def test_part_of_a_day():
    """A promise of 5.5 days takes 6 whole days"""
    assert estimate([Task("only", 5.5, 5.5, 5.5)], 10)[0] == 6
