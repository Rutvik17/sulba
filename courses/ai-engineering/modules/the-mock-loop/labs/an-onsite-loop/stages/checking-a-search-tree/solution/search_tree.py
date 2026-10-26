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
    waiting, node, last = [], root, None
    while waiting or node:
        while node:
            waiting.append(node)
            node = node.left
        node = waiting.pop()
        if last is not None and node.value <= last:
            return False
        last = node.value
        node = node.right
    return True
