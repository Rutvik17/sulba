import gc
import random
import tracemalloc

import pytest
from cycle import Node, cycle_start

NODES = 200_000
ALLOWED = 64 * 1024


# Every node a test makes, kept until the test ends.
kept = []


@pytest.fixture(autouse=True)
def unlinked():
    """Unlinks every node when a test ends, so that a long list is freed a node at a time."""
    yield
    for each in gc.get_objects():
        if type(each) is Node:
            each.next = None
    kept.clear()


def looped(length, start):
    """A list of length new nodes whose last points back to the node at start, or ends
    when start is None, and its nodes."""
    nodes = [Node(index) for index in range(length)]
    for node, following in zip(nodes, nodes[1:]):
        node.next = following
    if nodes and start is not None:
        nodes[-1].next = nodes[start]
    kept.extend(nodes)
    return nodes


@pytest.mark.id("tst_h1p5kb")
def test_cycle():
    """Finds where a cycle starts"""
    nodes = looped(4, 1)
    assert cycle_start(nodes[0]) is nodes[1]


@pytest.mark.id("tst_fz5o7m")
def test_edges():
    """Handles lists that end, a cycle through every node and a node pointing to itself"""
    assert cycle_start(None) is None
    assert cycle_start(looped(1, None)[0]) is None
    assert cycle_start(looped(5, None)[0]) is None
    whole = looped(5, 0)
    assert cycle_start(whole[0]) is whole[0]
    alone = looped(1, 0)
    assert cycle_start(alone[0]) is alone[0]
    tail = looped(6, 5)
    assert cycle_start(tail[0]) is tail[5]


@pytest.mark.id("tst_8j4uh2")
def test_every_start():
    """Finds the start of every cycle in short lists, and changes no node"""
    rng = random.Random(82)
    for _ in range(300):
        length = rng.randint(1, 40)
        start = rng.choice([None, *range(length)])
        nodes = looped(length, start)
        links = [node.next for node in nodes]
        found = cycle_start(nodes[0])
        assert found is (None if start is None else nodes[start])
        assert [node.next for node in nodes] == links


@pytest.mark.id("tst_qtsmrz")
def test_long():
    """Finds the start of a long list's cycle in time, in a few names of memory"""
    nodes = looped(NODES, NODES * 3 // 4)
    tracemalloc.start()
    try:
        found = cycle_start(nodes[0])
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert found is nodes[NODES * 3 // 4]
    assert peak < ALLOWED
