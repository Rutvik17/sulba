class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def serialise(root):
    """The tree from root as a str, which deserialise reads back."""
    raise NotImplementedError


def deserialise(text):
    """The root of a new tree like the one serialise wrote as text."""
    raise NotImplementedError
