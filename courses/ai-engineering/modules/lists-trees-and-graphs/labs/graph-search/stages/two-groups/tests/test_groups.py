import itertools
import random

import pytest
from groups import two_groups

PEOPLE = 100_000


def tried(people, dislikes):
    """Whether some split of the people into two groups keeps every pair apart, by trying
    them all."""
    return any(
        all(groups[first] != groups[second] for first, second in dislikes)
        for groups in itertools.product((0, 1), repeat=people)
    )


@pytest.mark.id("tst_vcwf7m")
def test_two_groups():
    """Splits a team that can be split, and not one that can't"""
    assert two_groups(4, [(0, 1), (0, 2), (1, 3)]) is True
    assert two_groups(3, [(0, 1), (1, 2), (0, 2)]) is False


@pytest.mark.id("tst_mdwtg9")
def test_edges():
    """Splits a team without dislikes, finds a clash in any part, and can't place a person
    who dislikes themselves"""
    assert two_groups(0, []) is True
    assert two_groups(5, []) is True
    assert two_groups(6, [(0, 1), (3, 4), (4, 5), (5, 3)]) is False
    assert two_groups(2, [(1, 1)]) is False
    assert two_groups(4, [(0, 1), (1, 2), (2, 3), (3, 0)]) is True


@pytest.mark.id("tst_metdzg")
def test_random():
    """Matches trying every split, on random teams"""
    rng = random.Random(107)
    for _ in range(300):
        people = rng.randint(1, 9)
        dislikes = [
            (rng.randrange(people), rng.randrange(people))
            for _ in range(rng.randint(0, people + 2))
        ]
        assert two_groups(people, dislikes) == tried(people, dislikes)


@pytest.mark.id("tst_ya7z77")
def test_long():
    """Splits a large team in time"""
    ring = [(person, (person + 1) % PEOPLE) for person in range(PEOPLE)]
    assert two_groups(PEOPLE, ring) is True
    assert two_groups(PEOPLE, ring + [(0, 2)]) is False
