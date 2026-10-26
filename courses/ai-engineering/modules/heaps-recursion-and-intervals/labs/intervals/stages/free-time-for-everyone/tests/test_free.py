import random

import pytest

from free import free_time

PEOPLE = 1_000
EACH = 200
SPAN = 10**9


def schedule(rng, count, span):
    """count sorted busy times that don't overlap, within 0 to span."""
    ends = sorted(rng.sample(range(span), 2 * count))
    return [(ends[2 * n], ends[2 * n + 1]) for n in range(count)]


def every_moment(schedules):
    """The free times, by marking every moment from the earliest start to the latest end."""
    busy = [interval for each in schedules for interval in each]
    if not busy:
        return []
    first = min(start for start, _ in busy)
    last = max(end for _, end in busy)
    taken = [
        any(start <= moment < end for start, end in busy)
        for moment in range(first, last)
    ]
    found, moment = [], first
    while moment < last:
        if taken[moment - first]:
            moment += 1
            continue
        until = moment
        while until < last and not taken[until - first]:
            until += 1
        found.append((moment, until))
        moment = until
    return found


@pytest.mark.id("tst_bpmkyl")
def test_free_time():
    """Gives the times when no one is busy"""
    assert free_time([[(1, 2), (5, 6)], [(1, 3)], [(4, 10)]]) == [(3, 4)]
    assert free_time([[(1, 3), (6, 7)], [(2, 4)], [(2, 5), (9, 12)]]) == [
        (5, 6),
        (7, 9),
    ]


@pytest.mark.id("tst_crprdd")
def test_edges():
    """Handles no one, empty schedules, one person, and busy times that touch"""
    assert free_time([]) == []
    assert free_time([[], []]) == []
    assert free_time([[(1, 2), (4, 6)]]) == [(2, 4)]
    assert free_time([[(1, 3)], [(3, 5)]]) == []


@pytest.mark.id("tst_rc33ed")
def test_random():
    """Matches marking every moment, on random schedules"""
    rng = random.Random(541)
    for _ in range(300):
        schedules = [
            schedule(rng, rng.randint(0, 4), 30) for _ in range(rng.randint(0, 4))
        ]
        assert free_time(schedules) == every_moment(schedules)


@pytest.mark.id("tst_os0ciq")
def test_long():
    """Finds everyone's free time in time"""
    rng = random.Random(542)
    # Everyone is busy every hour but the free ones, the hours back to back.
    free = sorted(rng.sample(range(1, EACH - 1), 20))
    busy = [(100 * hour, 100 * hour + 100) for hour in range(EACH) if hour not in free]
    expected = []
    for hour in free:
        if expected and expected[-1][1] == 100 * hour:
            expected[-1] = (expected[-1][0], 100 * hour + 100)
        else:
            expected.append((100 * hour, 100 * hour + 100))
    assert free_time([list(busy) for _ in range(PEOPLE)]) == expected
    found = free_time([schedule(rng, EACH, SPAN) for _ in range(PEOPLE)])
    assert found == sorted(found)
    assert all(start < end for start, end in found)
