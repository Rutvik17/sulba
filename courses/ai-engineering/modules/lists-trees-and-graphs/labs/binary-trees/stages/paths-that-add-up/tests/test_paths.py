import random

import pytest
from paths import Node, count_paths

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


def brute(root, target):
    """The downward paths adding up to target, by walking down from every node."""
    count = 0
    for start, _ in depths(root):
        waiting = [(start, 0)]
        while waiting:
            node, total = waiting.pop()
            total += node.value
            count += total == target
            waiting += [(child, total) for child in (node.left, node.right) if child]
    return count


@pytest.mark.id("tst_orvo8g")
def test_paths():
    """Counts the downward paths that add up to a target"""
    root = Node(
        10,
        Node(5, Node(3, Node(3), Node(-2)), Node(2, None, Node(1))),
        Node(-3, None, Node(11)),
    )
    assert count_paths(root, 8) == 3


@pytest.mark.id("tst_7f8cud")
def test_edges():
    """Counts no paths in an empty tree, single nodes, zeros and negative values"""
    assert count_paths(None, 0) == 0
    assert count_paths(Node(4), 4) == 1
    assert count_paths(Node(0, Node(0)), 0) == 3
    assert count_paths(Node(-2, None, Node(-3)), -5) == 1


@pytest.mark.id("tst_pub6p3")
def test_random():
    """Matches walking down from every node, in random trees"""
    rng = random.Random(95)
    for _ in range(200):
        root = random_tree(rng, [rng.randint(-3, 3) for _ in range(rng.randint(1, 40))])
        target = rng.randint(-4, 4)
        assert count_paths(root, target) == brute(root, target)


@pytest.mark.id("tst_abw7ur")
def test_long():
    """Counts a large tree's paths in time"""
    root, _ = tall(lambda depth: 1 if depth % 2 == 0 else -1)
    # Values alternate down every path, so a path adds up to 0 when it has an even number of
    # nodes: a node at depth d ends (d + 1) // 2 of them.
    expected = sum((depth + 1) // 2 for _, depth in depths(root))
    assert count_paths(root, 0) == expected
