import random
from itertools import combinations

import pytest

from remove import fewest_removed

MEETINGS = 200_000


def every_set(meetings):
    """The fewest to remove, by trying every set of meetings to keep, largest first."""
    for size in range(len(meetings), -1, -1):
        for kept in combinations(sorted(meetings), size):
            if all(kept[n][1] <= kept[n + 1][0] for n in range(size - 1)):
                return len(meetings) - size
    return len(meetings)


@pytest.mark.id("tst_3997zs")
def test_fewest_removed():
    """Gives the fewest meetings to remove"""
    assert fewest_removed([(1, 2), (2, 3), (3, 4), (1, 3)]) == 1


@pytest.mark.id("tst_6croow")
def test_edges():
    """Handles no meetings, the same meeting three times, and meetings that touch"""
    assert fewest_removed([]) == 0
    assert fewest_removed([(1, 2), (1, 2), (1, 2)]) == 2
    assert fewest_removed([(1, 2), (2, 3)]) == 0
    assert fewest_removed([(1, 100), (11, 22), (1, 11), (2, 12)]) == 2


@pytest.mark.id("tst_jb3cdu")
def test_random():
    """Matches trying every set to keep, on random meetings"""
    rng = random.Random(521)
    for _ in range(300):
        meetings = [
            (start, start + rng.randint(1, 6))
            for start in (rng.randint(0, 20) for _ in range(rng.randint(0, 8)))
        ]
        assert fewest_removed(meetings) == every_set(meetings)


@pytest.mark.id("tst_ghcuxv")
def test_long():
    """Finds the fewest to remove from a long list in time"""
    rng = random.Random(522)
    # Back-to-back meetings, each with a longer one laid across the end of it.
    chain = [(10 * n, 10 * n + 10) for n in range(MEETINGS // 2)]
    across = [(10 * n + 5, 10 * n + 15) for n in range(MEETINGS // 2)]
    meetings = chain + across
    rng.shuffle(meetings)
    assert fewest_removed(meetings) == MEETINGS // 2
