class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def diameter(root):
    """The number of edges on the tree's longest path."""
    longest = 0

    def height(node):
        nonlocal longest
        if node is None:
            return 0
        left, right = height(node.left), height(node.right)
        longest = max(longest, left + right)
        return 1 + max(left, right)

    height(root)
    return longest
