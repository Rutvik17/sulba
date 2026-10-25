import itertools
import random

import pytest
from order import course_order

COURSES = 100_000


def keeps(order, courses, prerequisites):
    """Whether the order takes every course once, each after the courses it needs."""
    place = {course: index for index, course in enumerate(order)}
    return sorted(order) == list(range(courses)) and all(
        place[before] < place[course] for course, before in prerequisites
    )


def possible(courses, prerequisites):
    """Whether any order of the courses keeps every prerequisite, by trying them all."""
    return any(
        keeps(list(order), courses, prerequisites)
        for order in itertools.permutations(range(courses))
    )


@pytest.mark.id("tst_qjwyh8")
def test_course_order():
    """Orders the courses after their prerequisites"""
    prerequisites = [(1, 0), (2, 0), (3, 1), (3, 2)]
    assert keeps(course_order(4, prerequisites), 4, prerequisites)


@pytest.mark.id("tst_wjbd4c")
def test_edges():
    """Orders courses without prerequisites, and gives [] when courses need each other"""
    assert course_order(0, []) == []
    assert sorted(course_order(3, [])) == [0, 1, 2]
    assert course_order(2, [(0, 1), (1, 0)]) == []
    assert course_order(1, [(0, 0)]) == []
    assert course_order(4, [(1, 0), (2, 1), (3, 2), (1, 3)]) == []
    assert keeps(course_order(3, [(2, 0), (2, 0)]), 3, [(2, 0)])


@pytest.mark.id("tst_xqqnof")
def test_random():
    """Gives an order exactly when trying every order finds one, on random schools"""
    rng = random.Random(201)
    for _ in range(300):
        courses = rng.randint(1, 6)
        prerequisites = [
            (rng.randrange(courses), rng.randrange(courses))
            for _ in range(rng.randint(0, 7))
        ]
        order = course_order(courses, prerequisites)
        if possible(courses, prerequisites):
            assert keeps(order, courses, prerequisites)
        else:
            assert order == []


@pytest.mark.id("tst_eujchf")
def test_long():
    """Orders a long chain of courses in time"""
    chain = [(course, course - 1) for course in range(COURSES - 1, 0, -1)]
    assert course_order(COURSES, chain) == list(range(COURSES))
    assert course_order(COURSES, chain + [(0, COURSES - 1)]) == []
