class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def is_search_tree(root):
    """Whether every node's value is greater than every value in its left subtree and less than
    every value in its right subtree."""
    raise NotImplementedError
