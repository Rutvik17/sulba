import random

import pytest
from diameter import Node, diameter

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


def neighbours(root):
    """Each node of the tree mapped to the nodes an edge joins it to."""
    found = {}
    for node, _ in depths(root):
        found.setdefault(node, [])
        for child in (node.left, node.right):
            if child:
                found[node].append(child)
                found.setdefault(child, []).append(node)
    return found


def brute(root):
    """The longest distance between two nodes, by walking out from each node."""
    joined = neighbours(root)
    longest = 0
    for start in joined:
        seen, frontier, distance = {start}, [start], 0
        while frontier:
            longest = max(longest, distance)
            frontier = [
                near for node in frontier for near in joined[node] if near not in seen
            ]
            seen.update(frontier)
            distance += 1
    return longest


@pytest.mark.id("tst_srs5i7")
def test_diameter():
    """Counts the edges on the longest path"""
    root = Node(1, Node(2, Node(4), Node(5)), Node(3))
    assert diameter(root) == 3


@pytest.mark.id("tst_t99x5p")
def test_edges():
    """Gives 0 for no tree and one node, and finds a longest path below the root"""
    assert diameter(None) == 0
    assert diameter(Node(1)) == 0
    assert diameter(Node(1, Node(2, Node(3)))) == 2
    root = Node(1, Node(2, Node(3, Node(4)), Node(5, Node(6))))
    assert diameter(root) == 4


@pytest.mark.id("tst_emdzu1")
def test_random():
    """Matches the longest distance between two nodes, in random trees"""
    rng = random.Random(92)
    for _ in range(200):
        root = random_tree(rng, [0] * rng.randint(1, 40))
        assert diameter(root) == brute(root)


@pytest.mark.id("tst_rb9a7m")
def test_long():
    """Finds a large tree's diameter in time"""
    root, _ = tall(lambda depth: 0)
    assert diameter(root) == 2 * ARM
