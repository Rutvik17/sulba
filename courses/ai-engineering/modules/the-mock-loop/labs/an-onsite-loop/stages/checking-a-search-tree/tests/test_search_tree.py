import random

import pytest
from search_tree import Node, is_search_tree

ARM = 400
BUSH = 511


def bush():
    """A complete tree of BUSH new nodes."""
    nodes = [Node(None) for _ in range(BUSH)]
    for place, node in enumerate(nodes):
        if 2 * place + 2 < BUSH:
            node.left, node.right = nodes[2 * place + 1], nodes[2 * place + 2]
    return nodes[0]


def tall():
    """A tree whose root has two arms of ARM nodes, the left going left and the right going
    right, with a complete tree of BUSH nodes hanging from every arm node but each arm's last
    ten. Its values are unset."""
    root = Node(None)
    for side, other in (("left", "right"), ("right", "left")):
        arm, parent = [], root
        for _ in range(ARM):
            node = Node(None)
            setattr(parent, side, node)
            arm.append(node)
            parent = node
        for node in arm[:-10]:
            setattr(node, other, bush())
    return root


def random_tree(rng, size):
    """A tree of size new nodes of random shape, its values unset."""
    root = Node(None)
    free = [(root, "left"), (root, "right")]
    for _ in range(size - 1):
        parent, side = free.pop(rng.randrange(len(free)))
        node = Node(None)
        setattr(parent, side, node)
        free += [(node, "left"), (node, "right")]
    return root


def in_order(root):
    """The tree's nodes in order: each node's left subtree, the node, then its right subtree."""
    found, waiting, node = [], [], root
    while waiting or node:
        while node:
            waiting.append(node)
            node = node.left
        node = waiting.pop()
        found.append(node)
        node = node.right
    return found


def numbered(root, values):
    """The tree, with its nodes holding the values in order."""
    for node, value in zip(in_order(root), values, strict=True):
        node.value = value
    return root


def below(node):
    """The values in the subtree under node."""
    found, waiting = [], [node] if node else []
    while waiting:
        each = waiting.pop()
        found.append(each.value)
        waiting += [child for child in (each.left, each.right) if child]
    return found


def every_node_checked(root):
    """Whether the tree is a search tree, checking each node against every node below it."""
    return all(
        all(value < node.value for value in below(node.left))
        and all(value > node.value for value in below(node.right))
        for node in in_order(root)
    )


@pytest.mark.id("tst_ec4f2i")
def test_is_search_tree():
    """Tells a search tree from one with a value out of place below its parent"""
    assert is_search_tree(Node(5, Node(3, Node(2), Node(4)), Node(8, Node(7), Node(9))))
    assert not is_search_tree(Node(5, Node(3, None, Node(6)), Node(8)))


@pytest.mark.id("tst_j41osc")
def test_edges():
    """Handles an empty tree, one node, a repeated value and a long one-sided tree"""
    assert is_search_tree(None)
    assert is_search_tree(Node(1))
    assert not is_search_tree(Node(2, Node(2)))
    assert not is_search_tree(Node(2, None, Node(2)))
    chain = None
    for value in range(300):
        chain = Node(value, chain)
    assert is_search_tree(chain)
    chain = None
    for value in reversed(range(300)):
        chain = Node(value, chain)
    assert not is_search_tree(chain)


@pytest.mark.id("tst_bvw6bz")
def test_random():
    """Matches checking each node against every node below it, on random trees"""
    rng = random.Random(701)
    for _ in range(400):
        size = rng.randint(1, 30)
        values = sorted(rng.sample(range(100), size))
        if size > 1 and rng.random() < 0.7:
            first, second = rng.sample(range(size), 2)
            values[first], values[second] = values[second], values[first]
        root = numbered(random_tree(rng, size), values)
        assert is_search_tree(root) == every_node_checked(root)


@pytest.mark.id("tst_6xxdoi")
def test_long():
    """Checks a large tree in time"""
    root = tall()
    nodes = in_order(root)
    numbered(root, range(len(nodes)))
    assert is_search_tree(root)
    first, last = nodes[1000], nodes[-1000]
    first.value, last.value = last.value, first.value
    assert not is_search_tree(root)
