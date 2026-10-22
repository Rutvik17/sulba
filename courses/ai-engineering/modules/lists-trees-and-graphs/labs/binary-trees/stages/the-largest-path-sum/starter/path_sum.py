class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def largest_path_sum(root):
    """The largest sum of the values on any path of the tree."""
    raise NotImplementedError
