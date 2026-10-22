A downward path starts at any node and goes down through children to any node below it, or stops where it starts. Write `count_paths`:

```
count_paths(root, target) -> the number of downward paths whose values add up to target
```

For this tree and a target of 8, `count_paths` gives 3: 5 → 3, 5 → 2 → 1 and -3 → 11.

```
         10
        /  \
       5   -3
      / \    \
     3   2   11
    / \   \
   3  -2   1
```

Values are ints, which may be negative or 0. The tests' largest tree has {% $fig.nodes %} nodes in {% $fig.levels %} levels.
