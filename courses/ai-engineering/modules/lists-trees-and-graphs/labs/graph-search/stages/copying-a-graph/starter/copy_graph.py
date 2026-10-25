class Node:
    """A node of a graph: its value, and the nodes it links to."""

    def __init__(self, value, neighbours=None):
        self.value = value
        self.neighbours = neighbours if neighbours is not None else []


def copy_graph(node):
    """A copy of the graph that node is in, with every node it reaches copied once, and the
    copy of node."""
    raise NotImplementedError
