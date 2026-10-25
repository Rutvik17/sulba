A node's ancestors are the node itself, its parent, its parent's parent, and so on up to the root. Write `lowest_common_ancestor`:

```
lowest_common_ancestor(root, a, b) -> the deepest node that is an ancestor of both a and b
```

`a` and `b` are nodes of the tree, and may be the same node. For this tree, the lowest common ancestor of 6 and 4 is 5, and of 5 and 1 is 3:

```
        3
      /   \
     5     1
    / \   / \
   6   2 0   8
      / \
     7   4
```

Return the node itself, since values may repeat. The tests' largest tree has {% $fig.nodes %} nodes in {% $fig.levels %} levels.
