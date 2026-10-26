import random

import pytest
from delay import delay

COMPUTERS = 40_000
EXTRA = 80_000


def relaxed(computers, links, start):
    """The delay, by lowering each computer's time along every link until none changes."""
    far = float("inf")
    time = {computer: far for computer in range(1, computers + 1)}
    time[start] = 0
    for _ in range(computers):
        for source, target, minutes in links:
            if time[source] + minutes < time[target]:
                time[target] = time[source] + minutes
    latest = max(time.values())
    return -1 if latest == far else latest


@pytest.mark.id("tst_hgaf9y")
def test_delay():
    """Gives the minutes until every computer has the message"""
    assert delay(4, [(2, 1, 1), (2, 3, 1), (3, 4, 1)], 2) == 2
    assert delay(4, [(2, 1, 1), (2, 3, 1), (3, 4, 1)], 1) == -1


@pytest.mark.id("tst_s6hc6j")
def test_edges():
    """Takes the quicker of two ways, counts links of 0 minutes, and gives 0 for one computer"""
    assert delay(1, [], 1) == 0
    assert delay(2, [(1, 2, 5), (1, 2, 3)], 1) == 3
    assert delay(3, [(1, 2, 10), (1, 3, 1), (3, 2, 1)], 1) == 2
    assert delay(3, [(1, 2, 0), (2, 3, 0)], 1) == 0
    assert delay(2, [(2, 1, 1)], 1) == -1


@pytest.mark.id("tst_5hoc4d")
def test_random():
    """Matches lowering every computer's time along every link, on random networks"""
    rng = random.Random(207)
    for _ in range(300):
        computers = rng.randint(1, 8)
        links = [
            (rng.randint(1, computers), rng.randint(1, computers), rng.randint(0, 9))
            for _ in range(rng.randint(0, 20))
        ]
        start = rng.randint(1, computers)
        assert delay(computers, links, start) == relaxed(computers, links, start)


@pytest.mark.id("tst_5dg3ms")
def test_long():
    """Times a message across a large network in time"""
    rng = random.Random(208)
    chain = [(computer, computer + 1, 1) for computer in range(1, COMPUTERS)]
    extra = []
    for _ in range(EXTRA):
        a, b = rng.randint(1, COMPUTERS), rng.randint(1, COMPUTERS)
        # A link forward takes longer than the chain, and one back can't beat it either.
        extra.append((a, b, abs(b - a) + rng.randint(1, 50)))
    links = chain + extra
    rng.shuffle(links)
    assert delay(COMPUTERS, links, 1) == COMPUTERS - 1
    assert delay(COMPUTERS + 1, links, 1) == -1
