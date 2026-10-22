import gc
import tracemalloc

import pytest
from reorder import Node, reorder

NODES = 200_000
ALLOWED = 64 * 1024

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


def interleaved(items):
    """The items as first, last, second, second to last, and so on."""
    order = []
    low, high = 0, len(items) - 1
    while low <= high:
        order.append(items[low])
        if low != high:
            order.append(items[high])
        low, high = low + 1, high - 1
    return order


@pytest.mark.id("tst_vct2zx")
def test_reorder():
    """Reorders a list from both ends"""
    assert values(reorder(build([1, 2, 3, 4, 5]))) == [1, 5, 2, 4, 3]
    assert values(reorder(build([1, 2, 3, 4]))) == [1, 4, 2, 3]


@pytest.mark.id("tst_pk79ss")
def test_edges():
    """Reorders an empty list, one node and two"""
    assert reorder(None) is None
    assert values(reorder(build([1]))) == [1]
    assert values(reorder(build([1, 2]))) == [1, 2]


@pytest.mark.id("tst_jadjmg")
def test_every_length():
    """Relinks the list's own nodes for every short length"""
    for length in range(1, 40):
        head = build(list(range(length)))
        nodes = {}
        node = head
        while node is not None:
            nodes[node.value] = node
            node = node.next
        result = reorder(head)
        assert result is nodes[0]
        walked = []
        while result is not None and len(walked) <= length:
            walked.append(result)
            result = result.next
        assert walked == [nodes[value] for value in interleaved(list(range(length)))]


@pytest.mark.id("tst_eym9ww")
def test_long():
    """Reorders a long list in time, in a few names of memory"""
    head = build(list(range(NODES)))
    tracemalloc.start()
    try:
        head = reorder(head)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert values(head, most=NODES + 1) == interleaved(list(range(NODES)))
    assert peak < ALLOWED
