import random

import pytest
from codec import Node, deserialise, serialise

ARM = 400
BUSH = 511


def tall(value):
    """A tree whose root has two arms of ARM nodes, the left going left and the right going
    right, with a complete tree of BUSH nodes hanging from every arm node but each arm's last
    ten. Each node holds value(its depth). Gives the root and each arm's nodes."""
    root = Node(value(0))
    arms = []
    for side, other in (("left", "right"), ("right", "left")):
        arm, parent = [], root
        for depth in range(1, ARM + 1):
            node = Node(value(depth))
            setattr(parent, side, node)
            arm.append(node)
            parent = node
        for depth, node in enumerate(arm[:-10], start=1):
            setattr(node, other, bush(depth + 1, value))
        arms.append(arm)
    return root, arms


def bush(depth, value):
    """A complete tree of BUSH new nodes whose root is at depth, each holding value(its depth)."""
    nodes = [Node(value(depth + (place + 1).bit_length() - 1)) for place in range(BUSH)]
    for place, node in enumerate(nodes):
        if 2 * place + 2 < BUSH:
            node.left, node.right = nodes[2 * place + 1], nodes[2 * place + 2]
    return nodes[0]


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


def same(a, b):
    """Whether two trees have the same shape and values, and no node in common."""
    waiting = [(a, b)]
    while waiting:
        x, y = waiting.pop()
        if x is None or y is None:
            if x is not y:
                return False
            continue
        if x is y or x.value != y.value:
            return False
        waiting += [(x.left, y.left), (x.right, y.right)]
    return True


@pytest.mark.id("tst_2sp8j3")
def test_round_trip():
    """Gives back a copy of a tree"""
    root = Node(1, Node(2), Node(3, Node(4), Node(5)))
    text = serialise(root)
    assert isinstance(text, str)
    assert same(deserialise(text), root)


@pytest.mark.id("tst_9qqbqm")
def test_edges():
    """Copies an empty tree, negative values, and trees that differ only in shape"""
    assert deserialise(serialise(None)) is None
    root = Node(-10, None, Node(-3))
    assert same(deserialise(serialise(root)), root)
    left, right = Node(1, Node(2)), Node(1, None, Node(2))
    assert serialise(left) != serialise(right)
    assert same(deserialise(serialise(right)), right)


@pytest.mark.id("tst_si88yl")
def test_random():
    """Copies random trees"""
    rng = random.Random(94)
    for _ in range(200):
        root = random_tree(
            rng, [rng.randint(-1000, 1000) for _ in range(rng.randint(0, 40))]
        )
        assert same(deserialise(serialise(root)), root)


@pytest.mark.id("tst_25xfnk")
def test_long():
    """Copies a large tree in time"""
    root, _ = tall(lambda depth: 7 * depth - 1000)
    assert same(deserialise(serialise(root)), root)
