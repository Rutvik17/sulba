Write `reorder`:

```
reorder(head) -> head, its list relinked to take the first node, then the last, then the
    second, then the one before the last, and so on
```

`1 → 2 → 3 → 4 → 5` becomes `1 → 5 → 2 → 4 → 3`, and `1 → 2 → 3 → 4` becomes `1 → 4 → 2 → 3`. It relinks the nodes it's given, without a list or dict of them, and the head of an empty list is `None`.

The tests' longest list has {% $fig.nodes %} nodes.
