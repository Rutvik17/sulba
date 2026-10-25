```python
def diameter(root):
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
```

`height` gives the nodes on the longest way down from a node, from its children's heights. On the way, the longest path whose highest node is this one goes down both sides: `left + right` edges. Every path has a highest node, so the longest of these is the diameter. It's one walk over the nodes: time in proportion to them, and space for the tree's height, a call for each level.

Working out the heights of each node's two subtrees separately, at every node, walks each node again for every node above it. For the largest test's {% $fig.nodes %} nodes in {% $fig.levels %} levels, that's {% $fig.visits %} visits.
