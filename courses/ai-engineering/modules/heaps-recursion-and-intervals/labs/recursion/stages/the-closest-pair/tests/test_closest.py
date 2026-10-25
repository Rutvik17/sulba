import random

import pytest

from closest import closest

POINTS = 50_000


def every_pair(points):
    """The smallest squared distance, by checking every pair."""
    return min(
        (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
        for i, a in enumerate(points)
        for b in points[i + 1 :]
    )


@pytest.mark.id("tst_1llzcx")
def test_closest():
    """Gives the smallest squared distance between two points"""
    assert closest([(0, 0), (5, 5), (1, 1), (9, 0)]) == 2


@pytest.mark.id("tst_wjf9x2")
def test_edges():
    """Handles two points, the same point twice, points in a line and negative coordinates"""
    assert closest([(3, 4), (0, 0)]) == 25
    assert closest([(2, 2), (7, 1), (2, 2)]) == 0
    assert closest([(0, 0), (10, 0), (13, 0), (30, 0)]) == 9
    assert closest([(-5, -5), (5, 5), (-4, -7)]) == 5


@pytest.mark.id("tst_8n9jqm")
def test_random():
    """Matches checking every pair, on random points"""
    rng = random.Random(351)
    for _ in range(300):
        points = [
            (rng.randint(-20, 20), rng.randint(-20, 20))
            for _ in range(rng.randint(2, 40))
        ]
        assert closest(points) == every_pair(points)


@pytest.mark.id("tst_t8x6af")
def test_long():
    """Finds the closest pair of many points in time, scattered or along one line"""
    rng = random.Random(352)
    # Points 10 apart on a grid, and one more 5 from the first of them: no other pair is as close.
    places = rng.sample(range(1_000_000), POINTS - 1)
    points = [(10 * (place // 1_000), 10 * (place % 1_000)) for place in places]
    points.append((points[0][0] + 3, points[0][1] + 4))
    rng.shuffle(points)
    assert closest(points) == 25
    line = [(0, 2 * n) for n in range(POINTS)]
    rng.shuffle(line)
    assert closest(line) == 4
