import gc
import random

import pytest
from reverse import Node, reverse

NODES = 200_000

# Every node a test makes or walks, kept until the test ends.
kept = []


@pytest.fixture(autouse=True)
def unlinked():
    """Unlinks every node when a test ends, so that a long list is freed a node at a time."""
    yield
    for each in gc.get_objects():
        if type(each) is Node:
            each.next = None
    kept.clear()


def build(values):
    """A list of new nodes holding the values, and its head."""
    head = None
    for value in reversed(values):
        head = Node(value, head)
        kept.append(head)
    return head


def values(head, most=10**7):
    """The values from head on, stopping after most of them."""
    found = []
    while head is not None and len(found) < most:
        kept.append(head)
        found.append(head.value)
        head = head.next
    return found


@pytest.mark.id("tst_0dpa9p")
def test_reverse():
    """Reverses a list"""
    assert values(reverse(build([1, 2, 3]))) == [3, 2, 1]


@pytest.mark.id("tst_98k64l")
def test_same_nodes():
    """Relinks the list's own nodes"""
    head = build([1, 2, 3])
    nodes = [head, head.next, head.next.next]
    reversed_head = reverse(head)
    assert reversed_head is nodes[2]
    assert reversed_head.next is nodes[1]
    assert nodes[1].next is nodes[0]
    assert nodes[0].next is None


@pytest.mark.id("tst_24o9q1")
def test_edges():
    """Reverses an empty list, one node and lists of every short length"""
    assert reverse(None) is None
    assert values(reverse(build([7]))) == [7]
    rng = random.Random(81)
    for length in range(2, 30):
        items = [rng.randint(-9, 9) for _ in range(length)]
        assert values(reverse(build(items)), most=length + 1) == items[::-1]


@pytest.mark.id("tst_zrwr7r")
def test_long():
    """Reverses a long list in time"""
    head = reverse(build(list(range(NODES))))
    assert values(head, most=NODES + 1) == list(range(NODES - 1, -1, -1))
