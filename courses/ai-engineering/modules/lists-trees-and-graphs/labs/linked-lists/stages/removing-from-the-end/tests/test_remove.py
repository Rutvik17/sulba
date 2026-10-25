import gc
import random

import pytest
from remove import Node, remove_from_end

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


@pytest.mark.id("tst_ntl4hf")
def test_remove():
    """Removes the nth node from the end"""
    assert values(remove_from_end(build([1, 2, 3, 4, 5]), 2)) == [1, 2, 3, 5]


@pytest.mark.id("tst_d4qt1q")
def test_edges():
    """Removes the last node, the first node and a list's only node"""
    assert values(remove_from_end(build([1, 2, 3]), 1)) == [1, 2]
    head = build([1, 2, 3])
    second = head.next
    assert remove_from_end(head, 3) is second
    assert remove_from_end(build([9]), 1) is None


@pytest.mark.id("tst_u66msh")
def test_every_place():
    """Removes every place in short lists, keeping the other nodes"""
    rng = random.Random(83)
    for length in range(1, 25):
        for n in range(1, length + 1):
            items = [rng.randint(0, 99) for _ in range(length)]
            head = build(items)
            nodes = []
            node = head
            while node is not None:
                nodes.append(node)
                node = node.next
            kept = nodes[: length - n] + nodes[length - n + 1 :]
            result = remove_from_end(head, n)
            walked = []
            while result is not None and len(walked) <= length:
                walked.append(result)
                result = result.next
            assert walked == kept


@pytest.mark.id("tst_z5l01t")
def test_long():
    """Removes from a long list in time"""
    head = remove_from_end(build(list(range(NODES))), NODES // 2)
    expected = list(range(NODES))
    del expected[NODES - NODES // 2]
    assert values(head, most=NODES) == expected
