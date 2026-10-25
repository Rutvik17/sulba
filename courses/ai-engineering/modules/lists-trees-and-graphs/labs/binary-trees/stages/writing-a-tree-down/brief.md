Write `serialise` and `deserialise`, to keep a tree as text and get it back:

```
serialise(root) -> a str
deserialise(text) -> the root of a new tree with the shape and values of the one serialise
    was given
```

Values are ints, which may be negative. `deserialise(serialise(root))` is a copy of the tree, made of new nodes, and the copy of an empty tree is `None`. The text's form is yours to choose.

The tests' largest tree has {% $fig.nodes %} nodes in {% $fig.levels %} levels.
