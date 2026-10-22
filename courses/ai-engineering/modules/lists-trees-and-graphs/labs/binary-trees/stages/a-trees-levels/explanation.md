```python
def levels(root):
    found, level = [], [root] if root else []
    while level:
        found.append([node.value for node in level])
        level = [child for node in level for child in (node.left, node.right) if child]
    return found
```

Each level's list of nodes makes the next one from their children, in order, so each level reads left to right. Every node is visited once: time in proportion to the tree's nodes, and space for its widest level.

A queue of nodes works too, if it's a `collections.deque`. A list used as a queue, taking each node with `pop(0)`, is the slow way. Python's tutorial says why: "While appends and pops from the end of list are fast, doing inserts or pops from the beginning of a list is slow (because all of the other elements have to be shifted by one)." For the largest test's {% $fig.nodes %} nodes, the pops shift {% $fig.shifts %} items in all.
