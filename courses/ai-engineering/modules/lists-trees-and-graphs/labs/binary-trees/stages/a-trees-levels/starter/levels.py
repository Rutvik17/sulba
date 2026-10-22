class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def levels(root):
    """The tree's values, a list for each level from the root down, each read left to right."""
    raise NotImplementedError
