class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def lowest_common_ancestor(root, a, b):
    """The deepest node that is an ancestor of both a and b, each node its own ancestor."""
    raise NotImplementedError
