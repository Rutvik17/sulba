class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def largest_path_sum(root):
    """The largest sum of the values on any path of the tree."""
    largest = root.value

    def down(node):
        nonlocal largest
        if node is None:
            return 0
        left = max(down(node.left), 0)
        right = max(down(node.right), 0)
        largest = max(largest, node.value + left + right)
        return node.value + max(left, right)

    down(root)
    return largest
