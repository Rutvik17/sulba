Write `remove_from_end`:

```
remove_from_end(head, n) -> the head of the list without its nth node from the end
```

`n` is 1 for the last node, and at most the list's length. For `1 → 2 → 3 → 4 → 5` and `n` of 2, it returns the list `1 → 2 → 3 → 5`, its own nodes relinked. Removing the first node gives the second as the head, and removing a list's only node gives `None`.

The tests' longest list has {% $fig.nodes %} nodes.
