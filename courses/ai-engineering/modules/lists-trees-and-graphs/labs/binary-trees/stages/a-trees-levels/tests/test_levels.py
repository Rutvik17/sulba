import random

import pytest
from levels import Node, levels

LEVELS = 18
NODES = 2**LEVELS - 1


def random_tree(rng, values):
    """A tree of new nodes of random shape holding the values, the first at the root, and its
    root."""
    if not values:
        return None
    root = Node(values[0])
    free = [(root, "left"), (root, "right")]
    for value in values[1:]:
        parent, side = free.pop(rng.randrange(len(free)))
        node = Node(value)
        setattr(parent, side, node)
        free += [(node, "left"), (node, "right")]
    return root


def depths(root):
    """Each node of the tree with its depth, the root's being 0, in preorder: a node, then its
    left subtree, then its right."""
    found, waiting = [], [(root, 0)] if root else []
    while waiting:
        node, depth = waiting.pop()
        found.append((node, depth))
        waiting += [(child, depth + 1) for child in (node.right, node.left) if child]
    return found


def complete(count):
    """A tree of count new nodes filled level by level from the left, each holding its place in
    that order, and its root."""
    nodes = [Node(place) for place in range(count)]
    for place, node in enumerate(nodes):
        if 2 * place + 1 < count:
            node.left = nodes[2 * place + 1]
        if 2 * place + 2 < count:
            node.right = nodes[2 * place + 2]
    return nodes[0] if nodes else None


@pytest.mark.id("tst_05fjiu")
def test_levels():
    """Gives a tree's values level by level"""
    root = Node(3, Node(9), Node(20, Node(15), Node(7)))
    assert levels(root) == [[3], [9, 20], [15, 7]]


@pytest.mark.id("tst_3efimc")
def test_edges():
    """Gives no levels for an empty tree, one for a single node, and one a node for a chain"""
    assert levels(None) == []
    assert levels(Node(1)) == [[1]]
    assert levels(Node(1, None, Node(2, Node(3)))) == [[1], [2], [3]]


@pytest.mark.id("tst_o85h44")
def test_random():
    """Matches each node's depth, in order from the left, in random trees"""
    rng = random.Random(91)
    for _ in range(200):
        root = random_tree(rng, [rng.randint(-9, 9) for _ in range(rng.randint(1, 40))])
        by_depth = {}
        for node, depth in depths(root):
            by_depth.setdefault(depth, []).append(node.value)
        assert levels(root) == [by_depth[depth] for depth in range(len(by_depth))]


@pytest.mark.id("tst_u23a1h")
def test_long():
    """Gives a large tree's levels in time"""
    found = levels(complete(NODES))
    assert found == [
        list(range(2**level - 1, 2 ** (level + 1) - 1)) for level in range(LEVELS)
    ]
