class Node:
    """A node of a graph: its value, and the nodes it links to."""

    def __init__(self, value, neighbours=None):
        self.value = value
        self.neighbours = neighbours if neighbours is not None else []


def copy_graph(node):
    """A copy of the graph that node is in, with every node it reaches copied once, and the
    copy of node."""
    if node is None:
        return None
    copies = {node: Node(node.value)}
    waiting = [node]
    while waiting:
        original = waiting.pop()
        for neighbour in original.neighbours:
            if neighbour not in copies:
                copies[neighbour] = Node(neighbour.value)
                waiting.append(neighbour)
            copies[original].neighbours.append(copies[neighbour])
    return copies[node]
