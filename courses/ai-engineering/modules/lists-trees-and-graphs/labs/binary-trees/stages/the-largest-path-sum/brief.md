A path joins two nodes through the edges between parents and children, with no node twice, or is a single node. Write `largest_path_sum`:

```
largest_path_sum(root) -> the largest sum of the values on any path
```

For this tree, `largest_path_sum` gives 42, from the path 15 → 20 → 7:

```
    -10
    /  \
   9    20
       /  \
      15   7
```

The tree has at least one node, and values may be negative. The tests' largest tree has {% $fig.nodes %} nodes in {% $fig.levels %} levels.
