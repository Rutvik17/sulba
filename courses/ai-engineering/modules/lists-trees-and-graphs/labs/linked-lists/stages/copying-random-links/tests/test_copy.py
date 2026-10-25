import gc
import random

import pytest
from copy_list import Node, copy_list

NODES = 100_000


# Every node a test makes or walks, kept until the test ends.
kept = []


@pytest.fixture(autouse=True)
def unlinked():
    """Unlinks every node when a test ends, so that a long list is freed a node at a time."""
    yield
    for each in gc.get_objects():
        if type(each) is Node:
            each.next = each.random = None
    kept.clear()


def made(values, randoms):
    """A list of new nodes with the values, each node's random link the node at its place in
    randoms, or None, and its nodes."""
    nodes = [Node(value) for value in values]
    for node, following in zip(nodes, nodes[1:]):
        node.next = following
    for node, place in zip(nodes, randoms):
        node.random = None if place is None else nodes[place]
    kept.extend(nodes)
    return nodes


def shape(head, most):
    """The list's values, and each node's random link as a place in the list, or None."""
    nodes = []
    while head is not None and len(nodes) < most:
        nodes.append(head)
        head = head.next
    kept.extend(nodes)
    places = {id(node): place for place, node in enumerate(nodes)}
    return [node.value for node in nodes], [
        None if node.random is None else places.get(id(node.random), "outside")
        for node in nodes
    ]


@pytest.mark.id("tst_7dvf5x")
def test_copy():
    """Copies a list with random links"""
    nodes = made([7, 13, 11, 10, 1], [None, 0, 4, 2, 0])
    copy = copy_list(nodes[0])
    assert shape(copy, 10) == ([7, 13, 11, 10, 1], [None, 0, 4, 2, 0])


@pytest.mark.id("tst_10jo1w")
def test_new_nodes():
    """Makes new nodes and leaves the original as it was"""
    nodes = made([1, 1, 2], [2, 2, 1])
    before = shape(nodes[0], 10)
    copy = copy_list(nodes[0])
    copied = []
    while copy is not None:
        copied.append(copy)
        copy = copy.next
    assert not {id(node) for node in copied} & {id(node) for node in nodes}
    assert shape(nodes[0], 10) == before
    assert copy_list(None) is None
    alone = made([5], [0])
    assert shape(copy_list(alone[0]), 2) == ([5], [0])


@pytest.mark.id("tst_c4dei1")
def test_random_links():
    """Copies short lists with any random links"""
    rng = random.Random(86)
    for _ in range(300):
        length = rng.randint(1, 20)
        values = [rng.randint(0, 3) for _ in range(length)]
        randoms = [rng.choice([None, *range(length)]) for _ in range(length)]
        copy = copy_list(made(values, randoms)[0])
        assert shape(copy, length + 1) == (values, randoms)


@pytest.mark.id("tst_rvet4y")
def test_long():
    """Copies a long list in time"""
    randoms = [NODES // 2 + index % (NODES // 2) for index in range(NODES)]
    nodes = made(list(range(NODES)), randoms)
    assert shape(copy_list(nodes[0]), NODES + 1) == (list(range(NODES)), randoms)
