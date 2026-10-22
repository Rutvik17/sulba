A binary tree's nodes are `Node`s, each with a `value` and a `left` and `right` child, each a node or `None`. Write `levels`:

```
levels(root) -> the tree's values, a list for each level from the root down, each read left
    to right
```

For this tree, `levels` gives `[[3], [9, 20], [15, 7]]`:

```
    3
   / \
  9   20
     /  \
    15   7
```

The root of an empty tree is `None`, and it has no levels: `[]`.

The tests' largest tree has {% $fig.nodes %} nodes, in {% $fig.levels %} full levels.
