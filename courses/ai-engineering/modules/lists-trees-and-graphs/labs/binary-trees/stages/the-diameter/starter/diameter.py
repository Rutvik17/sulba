class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def diameter(root):
    """The number of edges on the tree's longest path."""
    raise NotImplementedError
