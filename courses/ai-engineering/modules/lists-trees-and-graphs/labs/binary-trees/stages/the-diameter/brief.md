A path joins two nodes through the edges between parents and children, with no node twice. Write `diameter`:

```
diameter(root) -> the number of edges on the tree's longest path
```

For this tree, `diameter` gives 3, the path from 4 or 5 through 2 and 1 to 3:

```
      1
     / \
    2   3
   / \
  4   5
```

The longest path needn't pass through the root. A tree of one node, or none, has a diameter of 0.

The tests' largest tree has {% $fig.nodes %} nodes in {% $fig.levels %} levels.
