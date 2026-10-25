```python
def largest_path_sum(root):
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
```

`down` gives the largest sum of a path that starts at the node and goes down, or stops there. A child's is worth taking only when it's above 0. The best path whose highest node is this one takes the node's value and both sides' best, and every path has a highest node, so the largest of these is the answer. A path of one node is its value with nothing from either side, so a tree whose values are all negative gives its largest value. It's one walk: time in proportion to the nodes, and space for the tree's height.

Working out the best ways down from each node's children separately, at every node, walks each node again for every node above it: for the largest test's {% $fig.nodes %} nodes in {% $fig.levels %} levels, {% $fig.visits %} visits.
