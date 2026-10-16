import random

import pytest
from rooms import rooms_needed

MEETINGS = 100_000


def by_counting(meetings):
    """The most meetings going on at once, counted at each start."""
    return max(
        (sum(1 for s, e in meetings if s <= start < e) for start, _ in meetings),
        default=0,
    )


@pytest.mark.id("tst_54mp12")
def test_rooms():
    """Finds the fewest rooms"""
    assert rooms_needed([(9, 10), (9, 12), (10, 11), (11, 13), (12, 14)]) == 2


@pytest.mark.id("tst_w69uv3")
def test_edges():
    """Reuses a room freed when the next meeting starts, and handles no meetings"""
    assert rooms_needed([(1, 2), (2, 3), (3, 4)]) == 1
    assert rooms_needed([(1, 4), (2, 5), (3, 6)]) == 3
    assert rooms_needed([(5, 6)]) == 1
    assert rooms_needed([]) == 0


@pytest.mark.id("tst_ihlpq4")
def test_counting():
    """Matches counting the meetings at each start"""
    rng = random.Random(58)
    for _ in range(300):
        meetings = []
        for _ in range(rng.randint(0, 9)):
            start = rng.randint(0, 12)
            meetings.append((start, start + rng.randint(1, 4)))
        assert rooms_needed(meetings) == by_counting(meetings)


@pytest.mark.id("tst_7of46g")
def test_long():
    """Finds the rooms for many meetings in time"""
    rng = random.Random(59)
    # A meeting starts at each time and lasts 1,000, so 1,000 are on at once.
    meetings = [(time, time + 1000) for time in range(MEETINGS)]
    rng.shuffle(meetings)
    assert rooms_needed(meetings) == 1000
