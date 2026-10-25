A list's nodes are `Node`s, each with a `value` and the `next` node, or `None` at the end. Write `reverse`:

```
reverse(head) -> the head of the list reversed, made of the same nodes
```

For `1 → 2 → 3`, `reverse` returns the node holding 3, with `3 → 2 → 1` after it. It relinks the nodes it's given rather than making new ones, and the head of an empty list is `None`.

The tests' longest list has {% $fig.nodes %} nodes.
