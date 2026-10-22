Each node of this list has a `random` link too, to any node of the list or to `None`. Write `copy_list`:

```
copy_list(head) -> the head of a copy of the list: new nodes with the same values, whose
    next and random links point to the copy's nodes as the original's point to the original's
```

If the original's third node's `random` is its first node, the copy's third node's `random` is the copy's first node. No node of the copy is a node of the original, and the original stays as it was.

The tests' longest list has {% $fig.nodes %} nodes.
