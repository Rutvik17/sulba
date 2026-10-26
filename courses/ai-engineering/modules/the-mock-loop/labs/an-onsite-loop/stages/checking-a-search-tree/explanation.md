```python
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
```

An in-order walk visits the left subtree, then the node, then the right subtree, so in a search tree it meets the values in strictly increasing order, and a tree whose in-order values strictly increase is a search tree. The walk keeps its own stack of the nodes whose left subtrees it is in, so a deep tree can't exhaust Python's recursion, and it stops at the first value that isn't larger than the last. It visits each node once, in time and space in proportion to the number of nodes and the tree's height.

Checking each node only against its two children misses a value out of place further down, as in the brief's tree. Checking each node against every node below it is right, but slow: the tests' largest tree makes {% $fig.visits %} comparisons.
