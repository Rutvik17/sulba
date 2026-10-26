import random

import pytest
from cables import extra_cable

COMPUTERS = 200_000


def is_tree(computers, cables):
    """Whether the cables join every computer from 1 to computers, with no loop."""
    if len(cables) != computers - 1:
        return False
    near = {computer: [] for computer in range(1, computers + 1)}
    for a, b in cables:
        near[a].append(b)
        near[b].append(a)
    seen, waiting = {1}, [1]
    while waiting:
        for other in near[waiting.pop()]:
            if other not in seen:
                seen.add(other)
                waiting.append(other)
    return len(seen) == computers


def taken_out(cables):
    """The latest cable without which the rest make a tree, by trying each from the last."""
    for place in range(len(cables) - 1, -1, -1):
        if is_tree(len(cables), cables[:place] + cables[place + 1 :]):
            return cables[place]
    raise AssertionError("No cable would do.")


def office(rng, computers):
    """A random tree of cables over the computers, with one more cable, which may run beside
    another, all in a random order."""
    cables = [(rng.randint(1, child - 1), child) for child in range(2, computers + 1)]
    cables.append(tuple(rng.sample(range(1, computers + 1), 2)))
    rng.shuffle(cables)
    names = list(range(1, computers + 1))
    rng.shuffle(names)
    return [(names[a - 1], names[b - 1]) for a, b in cables]


@pytest.mark.id("tst_7g2n09")
def test_extra_cable():
    """Finds the cable to take out"""
    assert extra_cable([(1, 2), (1, 3), (2, 3)]) == (2, 3)
    assert extra_cable([(1, 2), (2, 3), (3, 4), (1, 4), (1, 5)]) == (1, 4)


@pytest.mark.id("tst_qoj57u")
def test_edges():
    """Takes out the latest of the loop's cables, wherever it stands in the list"""
    assert extra_cable([(1, 2), (2, 1)]) == (2, 1)
    assert extra_cable([(2, 3), (1, 2), (3, 4), (3, 1)]) == (3, 1)
    assert extra_cable([(1, 4), (3, 4), (1, 3), (1, 2), (4, 5)]) == (1, 3)


@pytest.mark.id("tst_hdyf06")
def test_random():
    """Matches trying each cable from the last, in random offices"""
    rng = random.Random(204)
    for _ in range(300):
        cables = office(rng, rng.randint(2, 12))
        assert extra_cable(cables) == taken_out(cables)


@pytest.mark.id("tst_yhpeax")
def test_long():
    """Finds the extra cable in a large office in time"""
    chain = [(computer, computer + 1) for computer in range(1, COMPUTERS)]
    assert extra_cable(chain + [(COMPUTERS, 1)]) == (COMPUTERS, 1)
    reversed_ = [(computer + 1, computer) for computer in range(COMPUTERS - 1, 0, -1)]
    assert extra_cable(reversed_ + [(1, COMPUTERS)]) == (1, COMPUTERS)
