class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def lowest_common_ancestor(root, a, b):
    """The deepest node that is an ancestor of both a and b, each node its own ancestor."""
    if root is None or root is a or root is b:
        return root
    left = lowest_common_ancestor(root.left, a, b)
    right = lowest_common_ancestor(root.right, a, b)
    if left is not None and right is not None:
        return root
    return left if left is not None else right
