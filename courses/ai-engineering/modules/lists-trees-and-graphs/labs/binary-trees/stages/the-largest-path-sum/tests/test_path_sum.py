import random

import pytest
from path_sum import Node, largest_path_sum

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
    """The largest sum over every path, by walking out from each node."""
    joined = neighbours(root)
    largest = None
    for start in joined:
        waiting = [(start, None, 0)]
        while waiting:
            node, came_from, total = waiting.pop()
            total += node.value
            largest = total if largest is None else max(largest, total)
            waiting += [
                (near, node, total) for near in joined[node] if near is not came_from
            ]
    return largest


@pytest.mark.id("tst_ky2mgk")
def test_largest():
    """Finds the largest path sum"""
    root = Node(-10, Node(9), Node(20, Node(15), Node(7)))
    assert largest_path_sum(root) == 42


@pytest.mark.id("tst_1w8jog")
def test_edges():
    """Takes one node, all negative values, and a best path below the root"""
    assert largest_path_sum(Node(-3)) == -3
    assert largest_path_sum(Node(-2, Node(-1), Node(-3))) == -1
    assert largest_path_sum(Node(-10, Node(2, Node(3), Node(4)))) == 9


@pytest.mark.id("tst_m3ytf8")
def test_random():
    """Matches walking out from every node, in random trees"""
    rng = random.Random(96)
    for _ in range(200):
        root = random_tree(
            rng, [rng.randint(-10, 10) for _ in range(rng.randint(1, 30))]
        )
        assert largest_path_sum(root) == brute(root)


@pytest.mark.id("tst_1b148z")
def test_long():
    """Finds a large tree's largest path sum in time"""
    root, arms = tall(lambda depth: -1)
    for arm in arms:
        arm[-1].value = 1000
    # The best path joins the arms' ends: 1000 each, and -1 for each of the 2 * ARM - 1 nodes
    # between them.
    assert largest_path_sum(root) == 2000 - (2 * ARM - 1)
