```python
def count_paths(root, target):
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
```

`total` adds up the values from the root down to the node. A downward path ending at the node adds up to `total` minus the running total just above where it starts, so it adds up to `target` when that running total is `total - target`. `seen` counts the running totals on the way from the root, with 0 for the paths that start at the root, and each node's total is taken back out once its subtrees are done, so `seen` only ever holds the totals above the current node. Each node is visited once, with two dict lookups: time in proportion to the nodes, and space for the tree's height.

Starting a walk down from every node, adding as it goes, visits each node once for itself and once for every node above it: for the largest test's {% $fig.nodes %} nodes in {% $fig.levels %} levels, {% $fig.visits %} visits.
