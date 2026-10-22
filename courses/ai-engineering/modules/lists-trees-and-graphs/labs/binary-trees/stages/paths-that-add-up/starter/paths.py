class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def count_paths(root, target):
    """The number of downward paths whose values add up to target."""
    raise NotImplementedError
