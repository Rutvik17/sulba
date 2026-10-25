class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def count_paths(root, target):
    """The number of downward paths whose values add up to target."""
    seen = {0: 1}

    def walk(node, total):
        if node is None:
            return 0
        total += node.value
        found = seen.get(total - target, 0)
        seen[total] = seen.get(total, 0) + 1
        found += walk(node.left, total) + walk(node.right, total)
        seen[total] -= 1
        return found

    return walk(root, 0)
