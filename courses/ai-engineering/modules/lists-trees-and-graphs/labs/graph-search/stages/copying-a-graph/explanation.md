```python
def copy_graph(node):
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
```

The dict from originals to copies does two jobs. It's how a link finds the copy of a node another link already made, so two links to one node lead to one copy. And it's the search's record of the nodes seen, so a cycle ends when it comes back round. A node goes on the list once, when its copy is made, and its links are copied when it's taken off, so every node and every link is handled once: time and space in proportion to them.

Nodes work as dict keys as they are: by Python's data model, a class's default methods make "all objects compare unequal (except with themselves)", so two nodes with the same value are two keys. Copying each neighbour afresh, without the dict, never ends on a cycle, and calling the copy on each neighbour from inside itself follows the largest test's cycle {% $fig.nodes %} calls deep, past the recursion limit Python starts with.
