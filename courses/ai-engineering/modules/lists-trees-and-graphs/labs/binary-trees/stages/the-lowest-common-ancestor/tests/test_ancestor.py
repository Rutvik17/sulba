import random

import pytest
from ancestor import Node, lowest_common_ancestor

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


def brute(root, a, b):
    """The lowest common ancestor, walking up from b to the first of a's ancestors."""
    parent = {root: None}
    for node, _ in depths(root):
        for child in (node.left, node.right):
            if child:
                parent[child] = node
    above = set()
    while a is not None:
        above.add(a)
        a = parent[a]
    while b not in above:
        b = parent[b]
    return b


def leftmost(node):
    """The node reached by going left from node until there's no left child."""
    while node.left:
        node = node.left
    return node


@pytest.mark.id("tst_rnsbzu")
def test_ancestor():
    """Finds the lowest common ancestor"""
    n = {value: Node(value) for value in range(9)}
    n[3].left, n[3].right = n[5], n[1]
    n[5].left, n[5].right = n[6], n[2]
    n[2].left, n[2].right = n[7], n[4]
    n[1].left, n[1].right = n[0], n[8]
    assert lowest_common_ancestor(n[3], n[6], n[4]) is n[5]
    assert lowest_common_ancestor(n[3], n[5], n[1]) is n[3]


@pytest.mark.id("tst_tyrc6c")
def test_edges():
    """Gives a node that is the other's ancestor, the node itself, and the root"""
    leaf = Node(1)
    middle = Node(1, leaf)
    root = Node(1, middle, Node(1))
    assert lowest_common_ancestor(root, middle, leaf) is middle
    assert lowest_common_ancestor(root, leaf, leaf) is leaf
    assert lowest_common_ancestor(root, root.right, leaf) is root
    assert lowest_common_ancestor(root, root, root) is root


@pytest.mark.id("tst_j0ct9o")
def test_random():
    """Matches walking up from each node, in random trees with repeated values"""
    rng = random.Random(93)
    for _ in range(200):
        root = random_tree(rng, [rng.randint(0, 2) for _ in range(rng.randint(1, 30))])
        nodes = [node for node, _ in depths(root)]
        for _ in range(5):
            a, b = rng.choice(nodes), rng.choice(nodes)
            assert lowest_common_ancestor(root, a, b) is brute(root, a, b)


@pytest.mark.id("tst_stumnd")
def test_long():
    """Finds a lowest common ancestor deep in a large tree in time"""
    root, (left, _) = tall(lambda depth: depth)
    a, b = leftmost(left[379].right), leftmost(left[384].right)
    assert lowest_common_ancestor(root, a, b) is left[379]
    assert lowest_common_ancestor(root, b, left[-1]) is left[384]
