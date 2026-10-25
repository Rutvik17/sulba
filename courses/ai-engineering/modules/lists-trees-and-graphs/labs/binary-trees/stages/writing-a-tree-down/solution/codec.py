class Node:
    """A node of a binary tree: its value, and its left and right children, each a node or
    None."""

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def serialise(root):
    """The tree from root as a str, which deserialise reads back."""
    tokens, waiting = [], [root]
    while waiting:
        node = waiting.pop()
        if node is None:
            tokens.append("#")
        else:
            tokens.append(str(node.value))
            waiting += [node.right, node.left]
    return " ".join(tokens)


def deserialise(text):
    """The root of a new tree like the one serialise wrote as text."""
    tokens = iter(text.split())

    def build():
        token = next(tokens)
        if token == "#":
            return None
        node = Node(int(token))
        node.left = build()
        node.right = build()
        return node

    return build()
